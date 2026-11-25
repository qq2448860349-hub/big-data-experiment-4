"""Reproducible, self-created teaching data, not real shop records."""
import argparse
import hashlib
import json
import random
from pathlib import Path

GOODS = ("apple", "banana", "bread", "butter", "coffee", "diaper",
         "eggs", "juice", "milk", "rice", "tea", "yogurt")
GROUPS = (("bread", "butter", "milk", "eggs"),
          ("coffee", "milk", "bread"),
          ("apple", "banana", "yogurt", "juice"),
          ("diaper", "milk", "rice"),
          ("tea", "rice", "eggs"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="data")
    parser.add_argument("--rows", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=20261118)
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("rows must be positive")
    target = Path(args.directory)
    target.mkdir(parents=True, exist_ok=True)
    # Refuse accidental replacement of the supplied, hashed dataset.
    if any((target / name).exists() for name in ("transactions.txt", "manifest.json")):
        parser.error("Choose a new directory for regenerated data")
    rng = random.Random(args.seed)
    rows = []
    for _ in range(args.rows):
        goods = set(GROUPS[rng.randrange(len(GROUPS))])
        goods.update(item for item in GOODS if rng.randrange(100) < 12)
        rows.append(" ".join(sorted(goods)))
    content = ("\n".join(rows) + "\n").encode("utf-8")
    (target / "transactions.txt").write_bytes(content)
    manifest = {"source": "Self-created synthetic shopping baskets for teaching",
                "seed": args.seed, "transactions": args.rows, "goods": list(GOODS),
                "sha256": hashlib.sha256(content).hexdigest()}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
