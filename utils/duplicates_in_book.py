#!/usr/bin/env python
"""
Reads duplicates.log and produces duplicates_in_book.log:
  - keeps only groups where all duplicates belong to the same book
  - augments each entry with the line in the .tex book where it appears
  - sorts by book name, then hash
  - separates groups with a blank line

With --section: additionally filters to groups where all duplicates
  appear in the same .tex file (same part/section of the book).
"""

import sys
import glob
import argparse
import subprocess
from collections import defaultdict
from itertools import groupby


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


def tex_file_of(tex_ref):
    """Extract 'books/file.tex' from 'books/file.tex:linenum:match', or None if NA."""
    if tex_ref == 'NA':
        return None
    return tex_ref.split(':')[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?', default='duplicates.log')
    parser.add_argument('--section', action='store_true',
                        help='keep only groups appearing in the same .tex file')
    args = parser.parse_args()

    groups = parse_groups(args.input)

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
            rows.append((book, hash_val, tex_ref, f'{hash_val}\t{gnos_path}\t{tex_ref}'))

    # Sort by book name, then hash
    rows.sort(key=lambda r: (r[0], r[1]))

    if args.section:
        # Keep only groups where all entries appear in the same .tex file
        filtered = []
        for _, group in groupby(rows, key=lambda r: r[1]):
            group = list(group)
            tex_files = {tex_file_of(r[2]) for r in group} - {None}
            if len(tex_files) == 1:
                filtered.extend(group)
        rows = filtered

    # Output with blank lines between hash groups
    prev_hash = None
    for _, hash_val, _, line in rows:
        if prev_hash is not None and hash_val != prev_hash:
            print()
        print(line)
        prev_hash = hash_val


if __name__ == '__main__':
    main()
