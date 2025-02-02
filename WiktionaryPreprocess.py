import sys
import csv
import os
from collections import defaultdict

maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)

wiktionary_dump_path = input("Directory of the wiktionary dump(TSV format):")
"""
with open(wiktionary_dump_path, newline='') as wiktionary_file:
    wiktionaryReader = csv.reader(wiktionary_file, delimiter='\t', quotechar='"')
    for row in wiktionaryReader:
        firstLetter = row[1][0]
        with open(wiktionary_dump_path, newline='') as wiktionary_file
"""


def split_tsv_by_second_column(file_path):
    # Dictionary to hold rows for each two-character sequence and a combined single-character/slash entries
    groups = defaultdict(list)

    # Read the input TSV file
    with open(file_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter='\t')
        headers = next(reader, None)  # Read headers, if present

        for row in reader:
            if len(row) < 2:
                continue  # Skip rows that don't have at least 2 columns

            entry = row[1]
            if len(entry) >= 2:
                two_char_seq = entry[:2].upper()
                if '/' in two_char_seq:
                    # Group entries with '/' together with single-character entries
                    groups['single_char'].append(row)
                else:
                    groups[two_char_seq].append(row)
            else:
                # Group single-character entries separately
                groups['single_char'].append(row)

    # Write out the grouped TSV files
    for key, rows in groups.items():
        if key == 'single_char':
            output_file = 'Wiktionary_dump/single_char.tsv'
        else:
            output_file = f"Wiktionary_dump/{key}.tsv"

        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter='\t')
            if headers:
                writer.writerow(headers)  # Write headers if present
            writer.writerows(rows)

    print("TSV files created for each two-character sequence and single-character/slash entries.")

