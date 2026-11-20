# Group 9 — Graph Databases and Knowledge Graphs

**Research question:** When do graph models beat relational joins?

This repository supports the Group 9 DBMS research assignment comparing **Neo4j** with **PostgreSQL recursive CTEs** for multi-hop friends-of-friends traversal.

## Repository contents

- `dataset/` — starter CSV dataset (synthetic)
- `neo4j/` — graph creation and Cypher query scripts
- `postgresql/` — relational schema/setup and recursive SQL queries
- `benchmark/` — benchmark runner and Python dependencies
- `scripts/` — helper scripts
- `results/` — CSV templates and a place for actual results/screenshots
- `graphs/` — figures created from measured data
- `literature/` — literature matrix spreadsheet
- `report/` — article PDF
- `docs/` — benchmark instructions, viva/peer-review notes
- `docker-compose.yml` — optional local services configuration

## Quick start (online databases)

1. Create a free Neo4j Aura instance at https://console.neo4j.io/ and keep its credentials private.
2. Open the Cypher editor and run `neo4j/create_graph.cypher` (if using the included starter graph/data) and queries in `neo4j/queries.cypher`.
3. Open a PostgreSQL browser playground or your PostgreSQL server. Run `postgresql/setup.sql`, then queries from `postgresql/queries.sql`.
4. Compare that both systems return the same result set. Save screenshots in `results/screenshots/`.
5. Record measured timing and environment information in `results/experiment_results.csv`. Browser-playground timings are not controlled benchmarks and should be labelled exploratory.

## Reproducible benchmark runner

See `docs/benchmark_README.md` for the `bench.py` workflow. The benchmark runner can generate synthetic graph data or convert a SNAP edge list, load it to PostgreSQL and Neo4j, run multiple depths/repetitions, verify results against a Python reference traversal, and produce summaries/plots.

> **Status and honesty note:** The article PDF is included as received. It currently contains placeholders for experimental values and conclusions (for example `[X]`, `[Y]`, and bracketed graph-size/depth values). Replace these only after running the experiment and checking results. The benchmark's Python reference/dry-run is not evidence of database performance. No passwords or private credentials belong in this repository.

## Reproduce benchmark (local server setup)

Install dependencies from `benchmark/requirements.txt`, configure PostgreSQL and Neo4j, then follow the command examples in `docs/benchmark_README.md`. Report software versions, machine details, graph sizes, repetitions, and warm/cold conditions in the paper.

## Research article and supporting files

- `report/G9_Graph_Database_Article.pdf`
- `literature/G9_Literature_Matrix.xlsx`
- `docs/G9_Viva_and_Peer_Review.md`

## Team

Group 9 — add/confirm members, IDs, roles, and contributions before submission.

## Data and privacy

Starter data is synthetic. Do not upload personal information, database passwords, API keys, or private credentials. Cite any public dataset used and preserve its license/terms.
