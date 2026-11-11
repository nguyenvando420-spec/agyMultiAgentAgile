#!/usr/bin/env bash
# Chạy bộ đề benchmark trên nhiều model song song, ghi output + thời gian
set -u
B="$(cd "$(dirname "$0")" && pwd)"
MODELS=("$@")
for m in "${MODELS[@]}"; do
  (
    d="$B/runs/$m"; mkdir -p "$d"; cd "$d"
    start=$(date +%s)
    agy -p "$(cat "$B/prompt.md")" --model "$m" --print-timeout 1200s > "$d/output.md" 2> "$d/stderr.log"
    code=$?
    end=$(date +%s)
    echo "{\"model\":\"$m\",\"exit\":$code,\"seconds\":$((end-start))}" > "$d/meta.json"
  ) &
done
wait
echo "ALL DONE"
