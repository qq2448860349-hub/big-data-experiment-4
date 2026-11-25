"""Validate format and compare every itemset, exact integer count and file byte."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from mining import result_lines


def read_result(path, expected_total, minimum):
    entries = {}
    with open(path, encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != ["items", "count", "transactions", "support"]:
            raise ValueError("Invalid header: " + str(path))
        for row in reader:
            items = tuple(row["items"].split(","))
            count, total = int(row["count"]), int(row["transactions"])
            if (items != tuple(sorted(set(items))) or not all(items)
                    or items in entries or total != expected_total
                    or not minimum <= count <= total):
                raise ValueError("Invalid result row: " + str(row))
            entries[items] = count
    canonical = ("\n".join(result_lines(entries, expected_total)) + "\n").encode("utf-8")
    if Path(path).read_bytes() != canonical:
        raise ValueError("Result is not canonical or support is incorrect: " + str(path))
    return entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("serial")
    parser.add_argument("parallel")
    parser.add_argument("serial_metrics")
    parser.add_argument("parallel_metrics")
    args = parser.parse_args()
    serial_meta = json.loads(Path(args.serial_metrics).read_text(encoding="utf-8"))
    parallel_meta = json.loads(Path(args.parallel_metrics).read_text(encoding="utf-8"))
    for key in ("transactions", "min_count", "itemsets", "levels"):
        if serial_meta[key] != parallel_meta[key]:
            raise ValueError("Metrics differ: " + key)
    total, minimum = serial_meta["transactions"], serial_meta["min_count"]
    serial = read_result(args.serial, total, minimum)
    parallel = read_result(args.parallel, total, minimum)
    if serial != parallel or len(serial) != serial_meta["itemsets"]:
        raise ValueError("Frequent itemsets or support counts differ")
    if Path(args.serial).read_bytes() != Path(args.parallel).read_bytes():
        raise ValueError("Output bytes differ")
    print("MATCH: {} transactions; {} frequent itemsets; all counts and output bytes identical."
          .format(total, len(serial)))
    print("OUTPUT SHA256:", hashlib.sha256(Path(args.serial).read_bytes()).hexdigest())
    print("Serial seconds:", serial_meta["elapsed_seconds"])
    print("Spark seconds:", parallel_meta["elapsed_seconds"])
    print("Spark application:", parallel_meta["application_id"])


if __name__ == "__main__":
    main()
