"""Single-process Apriori, using only the Python standard library."""
import json
import time
from pathlib import Path
from mining import arguments, next_candidates, parse_transaction, result_lines, support_count


def mine(transactions, minimum):
    universe = sorted(set().union(*transactions))
    candidates = [(item,) for item in universe]
    frequent = {}
    levels = []
    while candidates:
        current = {}
        for candidate in candidates:
            goods = frozenset(candidate)
            count = sum(goods.issubset(transaction) for transaction in transactions)
            if count >= minimum:
                current[candidate] = count
        levels.append({"size": len(candidates[0]), "candidates": len(candidates),
                       "frequent": len(current)})
        print("SERIAL LEVEL", levels[-1], flush=True)
        frequent.update(current)
        candidates = next_candidates(current)
    return frequent, levels


def main():
    args = arguments("Single-process Apriori")
    started = time.perf_counter()
    with open(args.input, encoding="utf-8") as source:
        transactions = [basket for basket in map(parse_transaction, source) if basket]
    minimum = support_count(args.min_support, len(transactions))
    frequent, levels = mine(transactions, minimum)
    with open(args.output, "w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(result_lines(frequent, len(transactions))) + "\n")
    metrics = {"mode": "serial", "transactions": len(transactions),
               "min_count": minimum, "itemsets": len(frequent), "levels": levels,
               "elapsed_seconds": time.perf_counter() - started}
    Path(args.metrics).write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print("SERIAL COMPLETE:", json.dumps(metrics), flush=True)


if __name__ == "__main__":
    main()
