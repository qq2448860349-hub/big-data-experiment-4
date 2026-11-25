"""Independent exhaustive oracle for pruning and partition-count regressions."""
import itertools
import random
import tempfile
import unittest
from pathlib import Path
from collections import Counter
from mining import count_partition, next_candidates, parse_transaction, result_lines, support_count
from serial_apriori import mine
from verify_results import read_result


def exhaustive(rows, minimum):
    counts = Counter()
    for row in rows:
        for size in range(1, len(row) + 1):
            counts.update(itertools.combinations(sorted(row), size))
    return {items: count for items, count in counts.items() if count >= minimum}


def partitioned(rows, minimum):
    universe = sorted(set().union(*rows))
    candidates = [(item,) for item in universe]
    result = {}
    while candidates:
        counts = Counter()
        # Deliberately include an empty partition and uneven partitions.
        for part in (rows[:1], [], rows[1:3], rows[3:]):
            counts.update(dict(count_partition(iter(part), candidates)))
        current = {key: value for key, value in counts.items() if value >= minimum}
        result.update(current)
        candidates = next_candidates(current)
    return result


class Correctness(unittest.TestCase):
    def check_rows(self, rows, minimum):
        oracle = exhaustive(rows, minimum)
        self.assertEqual(mine(rows, minimum)[0], oracle)
        self.assertEqual(partitioned(rows, minimum), oracle)

    def test_four_itemsets_and_exact_boundary(self):
        self.check_rows([frozenset('abcd'), frozenset('abcd'), frozenset('a')], 2)

    def test_no_frequent_items(self):
        self.check_rows([frozenset('a'), frozenset('b')], 2)

    def test_repeated_items_and_blank_lines(self):
        self.assertEqual(parse_transaction('bread bread milk'), frozenset(('bread', 'milk')))
        self.assertFalse(parse_transaction('  '))

    def test_decimal_threshold_and_empty_input(self):
        self.assertEqual(support_count('0.07', 100), 7)
        self.assertEqual(support_count('0.151', 10), 2)
        for value in ('0', '-1', '1.01', 'NaN', 'Infinity'):
            with self.assertRaises(ValueError):
                support_count(value, 10)
        with self.assertRaises(ValueError):
            support_count('0.15', 0)

    def test_seeded_random_baskets(self):
        rng = random.Random(44)
        for _ in range(12):
            rows = [frozenset(item for item in 'abcdef' if rng.randrange(2)) for _ in range(23)]
            self.check_rows(rows, rng.randrange(1, 24))

    def test_result_validation_rejects_wrong_support_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'result.tsv'
            content = '\n'.join(result_lines({('bread',): 2}, 3)) + '\n'
            path.write_bytes(content.encode('utf-8'))
            self.assertEqual(read_result(path, 3, 2), {('bread',): 2})
            path.write_bytes(content.replace('0.6666666667', '0.9999999999').encode('utf-8'))
            with self.assertRaises(ValueError):
                read_result(path, 3, 2)
            path.write_bytes((content + content.splitlines()[1] + '\n').encode('utf-8'))
            with self.assertRaises(ValueError):
                read_result(path, 3, 2)


if __name__ == '__main__':
    unittest.main()
