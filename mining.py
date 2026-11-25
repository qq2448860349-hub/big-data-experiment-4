"""Shared input, Apriori candidate generation and exact result formatting."""
import argparse
import itertools
from collections import Counter
from decimal import Decimal, ROUND_CEILING


def parse_transaction(line):
    # One transaction per line. Repeated goods in a basket count once.
    return frozenset(line.strip().split())


def support_count(value, total):
    support = Decimal(value)
    if not support.is_finite() or not 0 < support <= 1:
        raise ValueError("min-support must be in (0, 1]")
    if total <= 0:
        raise ValueError("Input contains no nonempty transactions")
    return int((support * total).to_integral_value(rounding=ROUND_CEILING))


def next_candidates(previous):
    """Join frequent k-itemsets, then prune using all k-subsets."""
    ordered = sorted(previous)
    known = set(ordered)
    result = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            if left[:-1] != right[:-1]:
                continue
            candidate = left + (right[-1],)
            if all(subset in known for subset in itertools.combinations(candidate, len(left))):
                result.append(candidate)
    return result


def count_partition(transactions, candidates):
    prepared = [(candidate, frozenset(candidate)) for candidate in candidates]
    counts = Counter()
    for transaction in transactions:
        for candidate, goods in prepared:
            if goods.issubset(transaction):
                counts[candidate] += 1
    return counts.items()


def result_lines(frequent, total):
    yield "items\tcount\ttransactions\tsupport"
    for items, count in sorted(frequent.items(), key=lambda entry: (len(entry[0]), entry[0])):
        support = Decimal(count) / Decimal(total)
        yield "{}\t{}\t{}\t{:.10f}".format(
            ",".join(items), count, total, support
        )


def arguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--min-support", default="0.15")
    parser.add_argument("--metrics", required=True)
    return parser.parse_args()
