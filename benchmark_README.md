# G9 benchmark: Neo4j vs PostgreSQL recursive CTE (friends-of-friends)

Reproduces the experiment in the article *Neo4j versus PostgreSQL Recursive Queries for Multi-Hop
Friends-of-Friends Traversal on Social Graphs*. Public or synthetic data only; no personal data.

## Status
`bench.py` was dry-run only with the built-in `ref` engine (pure-Python BFS). The PostgreSQL and Neo4j
code paths have **not** been run against real servers: expect to fix small version-specific issues
(driver versions, Neo4j database name, authentication) the first time you run them.

## Setup
```bash
pip install -r requirements.txt
# PostgreSQL: create an empty database, e.g.  createdb g9
# Neo4j: start a server (Community is enough) and note its password
```
Record exact versions of PostgreSQL, Neo4j, Python and the drivers in your article (Section V).

## Run
```bash
# 1. Data: synthetic heavy-tailed graph, or a SNAP edge list (txt or txt.gz)
python bench.py gen --nodes 100000 --m 5 --out data/synth_m.csv
python bench.py gen --snap path/to/facebook_combined.txt.gz --out data/ego_facebook.csv

# 2. Load the same file into both systems (note the printed load time and size)
python bench.py load-pg  --edges data/synth_m.csv --pg-dsn "dbname=g9 user=postgres host=localhost"
python bench.py load-neo --edges data/synth_m.csv --neo-pass YOUR_PASSWORD

# 3. Benchmark (checks both systems against a Python BFS and aborts on any mismatch)
python bench.py run --edges data/synth_m.csv --dataset synth_m --depths 1 2 3 4 \
    --starts 10 --warmup 2 --reps 5 --neo-pass YOUR_PASSWORD

# 4. Cold runs: restart both services, then run again with --tag cold
python bench.py run ... --tag cold --warmup 0 --reps 1

# 5. Why is PostgreSQL slow or fast? Read the plan
python bench.py explain --start 123 --depth 3
#    In Neo4j Browser, run PROFILE on the Cypher query from the article.

# 6. Tables and figures for the article
python bench.py plot --tag warm --dataset synth_m
```
Repeat steps 1–3 for each graph size (e.g. 10^4, 10^5, 10^6 edges) using the same `results/results.csv`
so that Fig. 4 (latency vs size) has several points. Output: `results/results.csv` (raw rows),
`results/summary.csv` (median, p95 per system and depth, for Tables IV–V) and
`results/fig3_*.png`, `fig4_*.png`, `fig5_*.png`.

## Notes
- Defaults (10 start users per stratum, 2 warm-ups, 5 repetitions) are small so a first run finishes quickly. Raise them for the final numbers and report what you used.
- Both directions of every friendship are stored in both systems, so a directed traversal gives identical results.
- Memory settings (PostgreSQL `shared_buffers`, Neo4j page cache) must be set by you and reported in the article's configuration table.
- Never report numbers from the `ref` engine as results.
