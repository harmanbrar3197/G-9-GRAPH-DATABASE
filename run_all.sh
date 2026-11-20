#!/usr/bin/env bash
# One-command experiment. Needs Docker and `pip install -r requirements.txt`.
# NOT TESTED against real servers by the author: read the output and fix small issues if any.
set -euo pipefail
PG="dbname=g9 user=postgres password=pw host=localhost"
NP="password12345"
docker compose up -d
echo "Waiting 40 s for the databases to start..."; sleep 40

for N in 2000 20000 200000; do          # about 8e3, 8e4, 8e5 directed edges with m=5 (adjust to your machine)
  python bench.py gen --nodes $N --m 5 --out data/synth_$N.csv
  python bench.py load-pg  --edges data/synth_$N.csv --pg-dsn "$PG"
  python bench.py load-neo --edges data/synth_$N.csv --neo-pass "$NP"
  python bench.py run --edges data/synth_$N.csv --dataset synth_$N --pg-dsn "$PG" --neo-pass "$NP" \
        --depths 1 2 3 4 --starts 10 --warmup 2 --reps 5 --tag warm
done

# Cold runs on the last dataset: restart the services, no warm-up, one repetition
docker compose restart; sleep 40
python bench.py run --edges data/synth_200000.csv --dataset synth_200000 --pg-dsn "$PG" --neo-pass "$NP" \
        --depths 1 2 3 4 --starts 10 --warmup 0 --reps 1 --tag cold

python bench.py plot --tag warm --dataset synth_200000
echo "Done. Use results/summary.csv and results/fig*.png in the article. Also run: python bench.py explain --start <id> --depth 3"
