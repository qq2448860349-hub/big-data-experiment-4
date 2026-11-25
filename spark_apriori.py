"""Apriori with distributed integer support counting on Spark RDDs."""
import json
import operator
import time
from pathlib import Path
from mining import (arguments, count_partition, next_candidates,
                    parse_transaction, result_lines, support_count)


def main():
    from pyspark.sql import SparkSession
    from pyspark import StorageLevel

    args = arguments("Spark parallel Apriori")
    started = time.perf_counter()
    spark = SparkSession.builder.appName("experiment4-apriori").getOrCreate()
    sc = spark.sparkContext
    sc.setLogLevel("WARN")
    transactions = None
    try:
        # No collect of transaction data. Only candidates and counts reach the driver.
        transactions = (sc.textFile(args.input, minPartitions=4)
                        .map(parse_transaction).filter(bool)
                        .persist(StorageLevel.MEMORY_AND_DISK))
        total = transactions.count()
        minimum = support_count(args.min_support, total)
        universe = sorted(transactions.flatMap(list).distinct().collect())
        candidates = [(item,) for item in universe]
        frequent = {}
        levels = []
        compute_started = time.perf_counter()
        while candidates:
            broadcast = sc.broadcast(candidates)
            try:
                current = dict(transactions.mapPartitions(
                    lambda rows: count_partition(rows, broadcast.value)
                ).reduceByKey(operator.add).filter(
                    lambda item: item[1] >= minimum
                ).collect())
            finally:
                broadcast.destroy()
            levels.append({"size": len(candidates[0]), "candidates": len(candidates),
                           "frequent": len(current)})
            print("SPARK LEVEL", levels[-1], flush=True)
            frequent.update(current)
            candidates = next_candidates(current)
        compute_seconds = time.perf_counter() - compute_started
        lines = list(result_lines(frequent, total))
        sc.parallelize(lines, 1).saveAsTextFile(args.output)
        metrics = {"mode": "spark", "master": sc.master, "application_id": sc.applicationId,
                   "partitions": transactions.getNumPartitions(), "transactions": total,
                   "min_count": minimum, "itemsets": len(frequent), "levels": levels,
                   "counting_seconds": compute_seconds,
                   "elapsed_seconds": time.perf_counter() - started}
        Path(args.metrics).write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print("SPARK COMPLETE:", json.dumps(metrics), flush=True)
    finally:
        if transactions is not None:
            transactions.unpersist()
        spark.stop()


if __name__ == "__main__":
    main()
