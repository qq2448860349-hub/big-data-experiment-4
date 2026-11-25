#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
bash scripts/check_environment.sh
mkdir -p records
work="$(mktemp -d "$PWD/records/run-$(date +%Y%m%d-%H%M%S)-XXXXXX")"
base="/user/vboxuser/experiment4/$(basename "$work")"
echo "Run directory: $work"
echo "HDFS directory: $base"

run_experiment() {
    python3 serial_apriori.py data/transactions.txt "$work/serial.tsv" \
        --min-support 0.15 --metrics "$work/serial.json"
    hdfs dfs -mkdir -p /user/vboxuser/experiment4
    hdfs dfs -mkdir "$base"
    hdfs dfs -put data/transactions.txt "$base/transactions.txt"
    "$SPARK_HOME/bin/spark-submit" --master yarn --deploy-mode client \
        --num-executors 1 --executor-cores 2 --executor-memory 512m --driver-memory 512m \
        --conf spark.dynamicAllocation.enabled=false \
        --conf spark.pyspark.python=/usr/bin/python3 \
        --conf spark.ui.showConsoleProgress=false \
        --py-files "$PWD/mining.py" \
        "$PWD/spark_apriori.py" "hdfs://localhost:9000$base/transactions.txt" \
        "hdfs://localhost:9000$base/output" --min-support 0.15 \
        --metrics "$work/spark.json"
    hdfs dfs -test -e "$base/output/_SUCCESS"
    hdfs dfs -getmerge "$base/output" "$work/spark.tsv"
    python3 verify_results.py "$work/serial.tsv" "$work/spark.tsv" \
        "$work/serial.json" "$work/spark.json"
    head -n 16 "$work/spark.tsv"
    echo "EXPERIMENT4 PASS"
    echo "Results and logs: $work"
}

run_experiment 2>&1 | tee "$work/run.log"
