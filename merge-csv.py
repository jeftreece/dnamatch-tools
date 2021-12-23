#!/usr/bin/env python3
# The above line helps ensure that python3 is used in this script, when running
# under Linux. You can also run it as "python <this script>"

# Python3 is recommended, but it may run under python2

# Author: Jef Treece 2021
# License: GPLv3. See accompanying LICENSE file.
# No warranty. You are responsible for your use of this program.

# Purpose:
# Merge two or more .csv files to remove duplicate lines
#
# Run:
# - Run this program listing all csv files to merge and an output filename
#
# Example:
# merge-csv.py matchlist1.csv matchlist2.csv matchlist3.csv out.csv

import csv, os, six, sys

# python2 may not work with this script (untested), so print a warning
if six.PY2:
    print('This program is tested with Python 3.x, and you have Python 2.x.')
    print('This message is a warning; program continues to run.')
    print('Refer to https://www.python.org/downloads/')

# file names are listed on the command line; no other input is accepted
# the final file name is the output file and must not exist
filenames = sys.argv[1:-1]

# refuse to clobber a file - output file must not exist yet
if os.path.exists(sys.argv[-1]):
    print('Error: {} already exists.'.format(sys.argv[-1]))
    print('Remove it and re-run or use a different output file name')
    sys.exit(-1)

# loop through all input files
fieldnames = None
merged_output = set()
for fname in filenames:
    # make sure input appears to be .csv file
    lines = [l for l in open(fname, 'r').readlines() if not l.startswith('#')]
    try:
        dialect = csv.Sniffer().sniff(''.join(lines[0:100]))
    except:
        print('{} does not appear to contain csv data - aborting'.format(ff))
        raise

    with open(fname,'r') as csvfile:
        d = csv.DictReader(csvfile, dialect=dialect)

        # column headers are only taken from the first file encountered
        if not fieldnames:
            fieldnames = d.fieldnames

        # field names must match exactly
        if d.fieldnames != fieldnames:
            print('{} is not identical to {}'.format(fname,filenames[0]))
            print('Skipping it and continuing.')
            continue

        # add row to output if it doesn't already exist
        for row in d:
            merged_output.add(tuple(row.values()))


# save the result as a .csv
rowlen = len(fieldnames)
with open(sys.argv[-1], 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames)
    writer.writeheader()
    for vals in merged_output:
        rowd = {fieldnames[i]:vals[i] for i in range(rowlen)}
        writer.writerow(rowd)

print('Saved merged output to {}'.format(sys.argv[-1]))


