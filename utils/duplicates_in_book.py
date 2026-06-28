#!/usr/bin/env python
"""
Reads duplicates.log and produces duplicates_in_book.log:
  - keeps only groups where all duplicates belong to the same book
  - augments each entry with the line in the .tex book where it appears
  - sorts by book name, then hash
  - separates groups with a blank line
"""

import sys
import glob
import subprocess
from collections import defaultdict


def parse_groups(path):
    """Parse duplicates.log into {hash: [gnos_path, ...]}."""
    groups = defaultdict(list)
    for line in open(path):
        line = line.rstrip('\n')
        if line:
            hash_val, gnos_path = line.split(None, 1)
            groups[hash_val].append(gnos_path)
    return groups


def book_of(gnos_path):
    """Extract book name from 'problems/<book>/<id>/<num>.gnos'."""
    return gnos_path.split('/')[1]


def find_tex_ref(book, problem_id, problem_num):
    """
    Search for \\p{id}{num} in books/<book>*.tex.
    Returns 'file:linenum:match' or 'NA'.
    """
    pattern = f'\\p{{{problem_id}}}{{{problem_num}}}'
    for tex_file in sorted(glob.glob(f'books/{book}*.tex')):
        result = subprocess.run(
            ['grep', '-nF', pattern, tex_file],
            capture_output=True, text=True
        )
        if result.stdout:
            return f'{tex_file}:{result.stdout.splitlines()[0]}'
    return 'NA'


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'duplicates.log'

    groups = parse_groups(input_file)

    # Keep only groups where all entries belong to the same book
    same_book = {
        h: paths for h, paths in groups.items()
        if len({book_of(p) for p in paths}) == 1
    }

    # Augment each entry with its .tex reference
    rows = []
    for hash_val, paths in same_book.items():
        book = book_of(paths[0])
        for gnos_path in paths:
            _, _, problem_id, filename = gnos_path.split('/')
            problem_num = filename.removesuffix('.gnos')
            tex_ref = find_tex_ref(book, problem_id, problem_num)
            rows.append((book, hash_val, f'{hash_val}\t{gnos_path}\t{tex_ref}'))

    # Sort by book name, then hash
    rows.sort(key=lambda r: (r[0], r[1]))

    # Output with blank lines between hash groups
    prev_hash = None
    for _, hash_val, line in rows:
        if prev_hash is not None and hash_val != prev_hash:
            print()
        print(line)
        prev_hash = hash_val


if __name__ == '__main__':
    main()
