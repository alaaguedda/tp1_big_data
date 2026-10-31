#!/usr/bin/env bash
set -e

SAMPLE="${INPUT_FILE:-data/HIGGS_sample_1pct.csv}"

if [ ! -f "$SAMPLE" ]; then
  echo "ERROR: $SAMPLE not found. Mount the folder that contains HIGGS_sample_1pct.csv on /app/data."
  exit 1
fi

mkdir -p output

echo "== Step 1: profile and clean =="
python src/clean.py

echo "== Step 2: build dashboard =="
python src/dashboard.py

echo "== Analysis finished. Results are in /app/output =="

if [ "${SERVE:-0}" = "1" ]; then
  echo "== Serving the dashboard on port 8000 =="
  exec python -m http.server 8000 --directory output
fi
