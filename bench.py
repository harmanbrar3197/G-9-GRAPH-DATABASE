#!/usr/bin/env python3
"""G9 benchmark: friends-of-friends (k-hop) traversal, Neo4j vs PostgreSQL recursive CTE.

Subcommands:
  gen      create an edge list (synthetic heavy-tailed graph, or convert a SNAP file)
  load-pg  load the edge list into PostgreSQL (table knows(src, dst) + B-tree index)
  load-neo load the edge list into Neo4j (:Person)-[:KNOWS]->(:Person)
  run      time the queries, check result equality, write results/results.csv
  explain  print EXPLAIN (ANALYZE, BUFFERS) of the PostgreSQL query for one start user
  plot     make summary.csv and the figures from results.csv

The 'ref' engine (pure-Python BFS) needs no database: use it to dry-run the pipeline.
"""
import argparse, csv, gzip, os, random, statistics, sys, time
from collections import defaultdict

# ----------------------------------------------------------------- data
def read_edges(path):
    with open(path, newline="") as f:
        r = csv.reader(f); next(r)
        return [(int(a), int(b)) for a, b in r]

def adjacency(edges):
    adj = defaultdict(list)
    for a, b in edges: adj[a].append(b)
    return adj

def cmd_gen(a):
    rng = random.Random(a.seed)
    und = set()
    if a.snap:                                   # convert a SNAP edge list (txt or txt.gz)
        op = gzip.open if a.snap.endswith(".gz") else open
        with op(a.snap, "rt") as f:
            for line in f:
                if line.startswith("#") or not line.strip(): continue
                u, v = line.split()[:2]; u, v = int(u), int(v)
                if u != v: und.add((min(u, v), max(u, v)))
    else:                                        # Barabasi-Albert-style preferential attachment
        m = a.m; targets = list(range(m)); repeated = []
        for new in range(m, a.nodes):
            for t in set(targets):
                und.add((min(new, t), max(new, t)))
            repeated.extend(targets); repeated.extend([new] * m)
            targets = [rng.choice(repeated) for _ in range(m)]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="") as f:      # symmetric closure: both directions stored
        w = csv.writer(f); w.writerow(["src", "dst"])
        for u, v in sorted(und): w.writerow([u, v]); w.writerow([v, u])
    print(f"wrote {2*len(und)} directed edges for {len({x for e in und for x in e})} nodes -> {a.out}")

# ----------------------------------------------------------------- engines
class Ref:
    name = "ref"
    def __init__(s, a, edges): s.adj = adjacency(edges)
    def query(s, start, k):
        seen, frontier = {start}, [start]
        for _ in range(k):
            nxt = []
            for u in frontier:
                for v in s.adj.get(u, ()):
                    if v not in seen: seen.add(v); nxt.append(v)
            frontier = nxt
        return len(seen) - 1
    def close(s): pass

PG_SQL = """WITH RECURSIVE r(id, d) AS (
  SELECT dst, 1 FROM knows WHERE src = %(s)s
  UNION
  SELECT k.dst, r.d + 1 FROM r JOIN knows k ON k.src = r.id WHERE r.d < %(k)s)
SELECT count(DISTINCT id) FROM r WHERE id <> %(s)s"""

class PG:
    name = "postgres"
    def __init__(s, a, edges):
        import psycopg2
        s.c = psycopg2.connect(a.pg_dsn); s.c.autocommit = True
        s.cur = s.c.cursor()
        s.cur.execute("SET statement_timeout = %s", (int(a.timeout * 1000),))
    def query(s, start, k):
        s.cur.execute(PG_SQL, {"s": start, "k": k}); return s.cur.fetchone()[0]
    def close(s): s.c.close()

class Neo:
    name = "neo4j"
    def __init__(s, a, edges):
        from neo4j import GraphDatabase
        s.d = GraphDatabase.driver(a.neo_uri, auth=(a.neo_user, a.neo_pass))
        s.sess = s.d.session(database=a.neo_db); s.timeout = a.timeout
    def query(s, start, k):
        from neo4j import Query
        q = Query(f"MATCH (s:Person {{id: $sid}})-[:KNOWS*1..{int(k)}]->(f:Person) "
                  "WHERE f <> s RETURN count(DISTINCT f) AS n", timeout=s.timeout)
        return s.sess.run(q, sid=start).single()["n"]
    def close(s): s.sess.close(); s.d.close()

ENGINES = {"ref": Ref, "postgres": PG, "neo4j": Neo}

# ----------------------------------------------------------------- loading
def cmd_load_pg(a):
    import psycopg2
    c = psycopg2.connect(a.pg_dsn); c.autocommit = True; cur = c.cursor()
    t0 = time.perf_counter()
    cur.execute("DROP TABLE IF EXISTS knows; CREATE TABLE knows(src integer NOT NULL, dst integer NOT NULL)")
    with open(a.edges) as f: cur.copy_expert("COPY knows FROM STDIN WITH (FORMAT csv, HEADER true)", f)
    cur.execute("CREATE INDEX knows_src_dst_idx ON knows(src, dst)")
    cur.execute("VACUUM ANALYZE knows")
    t = time.perf_counter() - t0
    cur.execute("SELECT pg_total_relation_size('knows')/1048576.0")
    print(f"postgres load_time_s={t:.2f} size_mb={cur.fetchone()[0]:.1f}")

def cmd_load_neo(a):
    from neo4j import GraphDatabase
    edges = read_edges(a.edges); nodes = sorted({x for e in edges for x in e})
    d = GraphDatabase.driver(a.neo_uri, auth=(a.neo_user, a.neo_pass))
    t0 = time.perf_counter()
    with d.session(database=a.neo_db) as s:
        s.run("MATCH (n) DETACH DELETE n").consume()
        s.run("CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE").consume()
        for i in range(0, len(nodes), a.batch):
            s.run("UNWIND $ids AS i CREATE (:Person {id: i})", ids=nodes[i:i+a.batch]).consume()
        for i in range(0, len(edges), a.batch):
            rows = [{"a": x, "b": y} for x, y in edges[i:i+a.batch]]
            s.run("UNWIND $rows AS r MATCH (a:Person {id: r.a}), (b:Person {id: r.b}) "
                  "CREATE (a)-[:KNOWS]->(b)", rows=rows).consume()
        s.run("CALL db.awaitIndexes()").consume()
    print(f"neo4j load_time_s={time.perf_counter()-t0:.2f}  (check store size on disk separately)")
    print("For graphs above ~1M edges use neo4j-admin database import instead (much faster).")

# ----------------------------------------------------------------- running
def sample_starts(edges, per_stratum, seed):
    deg = defaultdict(int)
    for a, _ in edges: deg[a] += 1
    order = sorted(deg, key=deg.get)
    n = len(order); lo, hi = int(.25 * n), int(.95 * n)
    strata = {"low": order[:lo], "medium": order[lo:hi], "high": order[hi:]}
    rng = random.Random(seed)
    return [(name, u) for name, pool in strata.items()
            for u in rng.sample(pool, min(per_stratum, len(pool)))]

def cmd_run(a):
    edges = read_edges(a.edges); n_edges = len(edges)
    starts = sample_starts(edges, a.starts, a.seed)
    ref = Ref(a, edges)
    engines = [ENGINES[e](a, edges) for e in a.engines]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    new = not os.path.exists(a.out)
    with open(a.out, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["system","dataset","edges","k","stratum","start","rep","latency_ms","count","status","tag"])
        for k in a.depths:
            for stratum, s in starts:
                expect = ref.query(s, k)
                for e in engines:
                    for _ in range(a.warmup):
                        try: e.query(s, k)
                        except Exception: break
                    for rep in range(a.reps):
                        t0 = time.perf_counter(); status = "ok"
                        try: cnt = e.query(s, k)
                        except Exception as ex: cnt, status = -1, f"error:{type(ex).__name__}"
                        ms = (time.perf_counter() - t0) * 1000
                        if status == "ok" and cnt != expect:
                            sys.exit(f"MISMATCH {e.name} k={k} start={s}: got {cnt}, expected {expect}")
                        w.writerow([e.name, a.dataset, n_edges, k, stratum, s, rep, f"{ms:.3f}", cnt, status, a.tag])
                f.flush()
            print(f"depth {k} done")
    for e in engines: e.close()
    print("results ->", a.out)

def cmd_explain(a):
    import psycopg2
    c = psycopg2.connect(a.pg_dsn); cur = c.cursor()
    cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + PG_SQL, {"s": a.start, "k": a.depth})
    print("\n".join(r[0] for r in cur.fetchall()))

# ----------------------------------------------------------------- plotting
def p95(x): x = sorted(x); return x[min(len(x)-1, int(0.95 * len(x)))]

def cmd_plot(a):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    rows = [r for r in csv.DictReader(open(a.results)) if r["status"] == "ok" and r["tag"] == a.tag]
    if not rows: sys.exit("no rows for tag " + a.tag)
    def grp(keys):
        g = defaultdict(list)
        for r in rows: g[tuple(r[k] if k not in ("k","edges") else int(r[k]) for k in keys)].append(float(r["latency_ms"]))
        return g
    os.makedirs(a.outdir, exist_ok=True)
    with open(os.path.join(a.outdir, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["system","dataset","edges","k","median_ms","p95_ms","n"])
        for (s, d, e, k), v in sorted(grp(["system","dataset","edges","k"]).items()):
            w.writerow([s, d, e, k, f"{statistics.median(v):.3f}", f"{p95(v):.3f}", len(v)])
    systems = sorted({r["system"] for r in rows})
    ds = sorted({r["dataset"] for r in rows}); main = a.dataset or ds[0]
    # Fig 3: latency vs depth
    g = grp(["system","dataset","k"]); plt.figure(figsize=(4.2, 3))
    for s in systems:
        ks = sorted(k for (ss, d, k) in g if ss == s and d == main)
        plt.plot(ks, [statistics.median(g[(s, main, k)]) for k in ks], marker="o", label=s)
    plt.yscale("log"); plt.xlabel("Traversal depth k (hops)"); plt.ylabel("Median latency (ms)")
    plt.xticks(sorted({k for (_, d, k) in g if d == main})); plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(a.outdir, "fig3_latency_vs_depth.png"), dpi=300); plt.close()
    # Fig 4: latency vs graph size at chosen depth
    g = grp(["system","edges","k"]); kk = a.depth or max(k for (_, _, k) in g)
    plt.figure(figsize=(4.2, 3))
    for s in systems:
        es = sorted(e for (ss, e, k) in g if ss == s and k == kk)
        plt.plot(es, [statistics.median(g[(s, e, kk)]) for e in es], marker="o", label=s)
    plt.xscale("log"); plt.yscale("log"); plt.xlabel("Number of edges"); plt.ylabel(f"Median latency, k={kk} (ms)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(a.outdir, "fig4_latency_vs_size.png"), dpi=300); plt.close()
    # Fig 5: latency by degree stratum
    g = grp(["system","dataset","k","stratum"]); plt.figure(figsize=(4.2, 3))
    names = ["low", "medium", "high"]; wd = 0.8 / max(1, len(systems))
    for i, s in enumerate(systems):
        vals = [statistics.median(g[(s, main, kk, n)]) if (s, main, kk, n) in g else 0 for n in names]
        plt.bar([j + i * wd for j in range(3)], vals, wd, label=s)
    plt.xticks([j + wd * (len(systems)-1) / 2 for j in range(3)], names); plt.yscale("log")
    plt.xlabel("Start-user degree stratum"); plt.ylabel(f"Median latency, k={kk} (ms)")
    plt.legend(); plt.tight_layout(); plt.savefig(os.path.join(a.outdir, "fig5_latency_by_degree.png"), dpi=300)
    print("wrote summary.csv and fig3/fig4/fig5 in", a.outdir)

# ----------------------------------------------------------------- cli
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    def conn(x):
        x.add_argument("--pg-dsn", default="dbname=g9 user=postgres host=localhost")
        x.add_argument("--neo-uri", default="bolt://localhost:7687"); x.add_argument("--neo-user", default="neo4j")
        x.add_argument("--neo-pass", default="password"); x.add_argument("--neo-db", default="neo4j")
    g = sp.add_parser("gen"); g.add_argument("--snap"); g.add_argument("--nodes", type=int, default=10000)
    g.add_argument("--m", type=int, default=5); g.add_argument("--seed", type=int, default=42)
    g.add_argument("--out", default="data/edges.csv"); g.set_defaults(f=cmd_gen)
    l = sp.add_parser("load-pg"); l.add_argument("--edges", default="data/edges.csv"); conn(l); l.set_defaults(f=cmd_load_pg)
    n = sp.add_parser("load-neo"); n.add_argument("--edges", default="data/edges.csv"); n.add_argument("--batch", type=int, default=10000); conn(n); n.set_defaults(f=cmd_load_neo)
    r = sp.add_parser("run"); conn(r); r.add_argument("--edges", default="data/edges.csv")
    r.add_argument("--dataset", default="synthetic"); r.add_argument("--engines", nargs="+", default=["neo4j","postgres"], choices=list(ENGINES))
    r.add_argument("--depths", nargs="+", type=int, default=[1,2,3,4]); r.add_argument("--starts", type=int, default=10, help="start users per degree stratum")
    r.add_argument("--warmup", type=int, default=2); r.add_argument("--reps", type=int, default=5)
    r.add_argument("--timeout", type=float, default=60); r.add_argument("--seed", type=int, default=42)
    r.add_argument("--tag", default="warm", help="label such as warm or cold"); r.add_argument("--out", default="results/results.csv"); r.set_defaults(f=cmd_run)
    e = sp.add_parser("explain"); conn(e); e.add_argument("--start", type=int, required=True); e.add_argument("--depth", type=int, default=3); e.set_defaults(f=cmd_explain)
    q = sp.add_parser("plot"); q.add_argument("--results", default="results/results.csv"); q.add_argument("--outdir", default="results")
    q.add_argument("--tag", default="warm"); q.add_argument("--dataset"); q.add_argument("--depth", type=int); q.set_defaults(f=cmd_plot)
    a = p.parse_args(); a.f(a)

if __name__ == "__main__": main()
