#!/usr/bin/env python3
"""Find SGF files with duplicate board positions within each book."""
import os
import re
import sys
from collections import defaultdict


def board_key(sgf_content: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ab_match = re.search(r"AB(\[[a-z]{2}\])+", sgf_content)
    aw_match = re.search(r"AW(\[[a-z]{2}\])+", sgf_content)
    ab = tuple(sorted(re.findall(r"\[([a-z]{2})\]", ab_match.group(0)))) if ab_match else ()
    aw = tuple(sorted(re.findall(r"\[([a-z]{2})\]", aw_match.group(0)))) if aw_match else ()
    return (ab, aw)


def check_book(book_dir: str) -> int:
    groups: dict[tuple, list[str]] = defaultdict(list)

    for root, dirs, files in os.walk(book_dir):
        dirs.sort()
        for fname in sorted(files):
            if not fname.endswith(".sgf"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path) as f:
                    key = board_key(f.read())
                groups[key].append(path)
            except Exception as e:
                print(f"  error reading {path}: {e}", file=sys.stderr)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if duplicates:
        print(f"\n{book_dir}")
        for paths in sorted(duplicates.values()):
            print(f"  {' == '.join(paths)}")
    return len(duplicates)


def main() -> None:
    if len(sys.argv) > 1:
        books = sys.argv[1:]
    else:
        problems_dir = "problems"
        books = sorted(
            os.path.join(problems_dir, d)
            for d in os.listdir(problems_dir)
            if os.path.isdir(os.path.join(problems_dir, d))
        )
    total = sum(check_book(b) for b in books)
    print(f"\n{total} duplicate position(s) found across {len(books)} book(s).")


if __name__ == "__main__":
    main()