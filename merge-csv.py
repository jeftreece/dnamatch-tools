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

# constants for readability - there is no need to change these lines
KEEP_ALL = 0
KEEP_NEWEST_NONBLANK = 1  # keep newest values, but only if non-blank
KEEP_NEWEST_ROW = 2  # keep row with the newest timestamp
KEEP_OLDEST_ROW = 3  # keep row with oldest timestamp

# === SECTION YOU MAY WISH TO CHANGE ===

# Things that affect how the program runs (you may wish to change)

# Check all files for csv dialect; if False, only check the first input file,
# and assume that all input files are the same dialect. Sniffing the dialect is
# time-consuming, and typically the default setting of False is best.
csv_dialect_sniff_all = False

# Columns that can differ and not be considered distinct rows. If a column is
# listed here, differing values in the column will be reduced down to a single
# value. For example, if you merge multiple .csv files having a Notes column,
# and that column differs between .csv files, you might want only the
# most-recent of the multiple rows to remain in the final output. With the
# (default) KEEP_ALL behavior, this list is of no consequence and is ignored.
differing_column_ok = [
    "Paternal Grandfather Birth Country",
    "Maternal Grandfather Birth Country",
    "Paternal Grandmother Birth Country",
    "Maternal Grandmother Birth Country",
    "Display Name",
    "Birth Year",
    "Set Relationship",
    "Maternal Side",
    "Paternal Side",
    "Maternal Haplogroup",
    "Paternal Haplogroup",
    "Family Surnames",
    "Family Locations",
    "Notes",
    "Sharing Status",
    "Showing Ancestry Results",
    "Family Tree URL"
    ]

# What to do when a differing column from the list above is found.
# The default setting is KEEP_ALL to keep all rows that are distinct
#
# Important note: KEEP_NEWEST and KEEP_OLDEST are based on the modification
# date of the input .csv file, which is typically when you downloaded the file
# originally. If you have modified the file since downloading it, this
# modification date is when the file was last changed.
differing_column_action = KEEP_ALL

# === END SECTION YOU MAY WISH TO CHANGE ===

import csv, os, six, sys, zipfile, gzip, io

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

# Helper routine to open a csv file and return the lines contained in it.
# The .csv file may be in a .zip file or gzipped or plain text
def get_filelines(f):
    try:
        if f.lower().endswith('.csv.gz'):
            with gzip.open(f, 'rt') as gf:
                lines = [l for l in gf.readlines() if not l.startswith('#')]
        elif f.lower().endswith('.zip'):
            with zipfile.ZipFile(f) as zf:
                for info in zf.filelist:
                    csvf = info.filename
                    if csvf.lower().endswith('.txt') or csvf.lower().endswith('.csv'):
                        break
                with zf.open(csvf) as fname:
                    textfile = io.TextIOWrapper(fname, encoding='utf8')
                    lines = [str(l) for l in textfile.readlines()
                             if not l.startswith('#')]
        elif f.lower().endswith('.csv') or f.lower().endswith('.txt'):
            lines = [l for l in open(f, 'r').readlines() if not l.startswith('#')]
        else:
            print('Skipping unrecognized file {} of type: {} - use .csv, .txt, or .zip'.format(f))
            return None
    except IOError as ioe:
        if ioe.errno == errno.ENOENT:
            print('Could not find {} - check file name and readability.'.format(f))
            return None
        else:
            print('There may be a problem with {} - did not read it.'.format(f))
            return None
    except TypeError:
        print('There was a problem processing {} - try unzipping it.'.format(f))
        # raise
        return None
    except Exception as e:
        print('Error "{}" happened while processing {} - continuing.'.format(e,f))
        return None
    return lines

# Helper routine for row merging of values that are OK to differ
# One of two rows is returned, based on the selection criteria (e.g.: newest)
# The first row item is a timestamp
def select_row(row1, row2):
    if differing_column_action == KEEP_NEWEST_ROW:
        if row1[0] < row2[0]:
            return(row2)
        return(row1)
    elif differing_column_action == KEEP_OLDEST_ROW:
        if row1[0] < row2[0]:
            return(row1)
        return(row2)
    elif differing_column_action == KEEP_NEWEST_NONBLANK:
        if row1[0] < row2[0]: # prefer row2 (newest) if it has a value
            return [row2[i] if row2[i] != "" else row1[i]
                        for i in range(len(row2))]
        else: # prefer row1 (newest) if it has a value
            return [row1[i] if row1[i] != "" else row2[i]
                        for i in range(len(row1))]
    # default action
    if len(row1) > 1:
        print('Unrecognized action in duplicate handling - using default action')
    return(row1)

# report what is being retained in the output file
if differing_column_action == KEEP_ALL:
    differing_column_ok = []
    print('Keeping all of the distinct rows in the output')
elif differing_column_action == KEEP_NEWEST_ROW:
    print('Keeping only the newest row if certain columns change')
elif differing_column_action == KEEP_OLDEST_ROW:
    print('Keeping only the oldest row if certain columns change')
elif differing_column_action == KEEP_NEWEST_NONBLANK:
    print('Keeping only the newest non-blank values if certain columns change')
    
# loop through all input files
fieldnames = None
merged_output = {}
dialect = None
key_fields = None
changed_fields = None
for fname in filenames:
    # make sure input appears to be .csv file
    lines = get_filelines(fname)
    if (not dialect) or csv_dialect_sniff_all:
        try:
            print('Detecting what sort of .csv file this is...')
            dialect = csv.Sniffer().sniff(''.join(lines))
            # quote character can be problematic; assume escaped by double-quoting
            dialect.doublequote = True
            dialect.quoting = csv.QUOTE_MINIMAL
            dialect.delimiter = ','
            dialect.quotechar = '"'
        except:
            print('{} does not appear to contain csv data - aborting'.format(fname))
            raise

    modtime = os.path.getmtime(fname)
    d = csv.DictReader(lines, dialect=dialect)

    # column headers are only taken from the first file encountered
    if not fieldnames:
        fieldnames = d.fieldnames
        # the colunm names that must be unique
        key_fields = tuple(set(fieldnames) - set(differing_column_ok))
        # the column names that can change between input files
        changed_fields = tuple(set(fieldnames).intersection(set(differing_column_ok)))
        print('Key fields: {}'.format(key_fields))
        print('Changed fields: {}'.format(changed_fields))

    # field names must match exactly
    if d.fieldnames != fieldnames:
        print('{} is not identical to {}'.format(fname,filenames[0]))
        print('Skipping it and continuing.')
        continue

    # add row to output if it doesn't already exist
    # replace previous row if changed fields meet criteria
    for row in d:
        # the output row is both the key (columns that must be unique)
        # and the fungible columns (columns that are allowed to change)
        key = tuple([row[c] for c in key_fields])
        val = tuple([modtime,] + [row[c] for c in changed_fields])
        try:
            changed_row = merged_output[key]
            out_row = select_row(changed_row, val)
            merged_output[key] = out_row
        except KeyError:
            # have not stored this row yet - store it
            merged_output[key] = val

    print('finished reading lines from {}'.format(fname))


# save the result as a .csv
rowlen = len(fieldnames)
tmp = list(merged_output)
with open(sys.argv[-1], 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames)
    writer.writeheader()
    for key in merged_output:
        # write out the key fields and the changeable fields
        d1 = {key_fields[i]:key[i] for i in range(len(key_fields))}
        d2 = {changed_fields[j]:merged_output[key][j+1]
                  for j in range(len(changed_fields))}
        rowd = {**d1, **d2}
        writer.writerow(rowd)

print('Saved merged output to {}'.format(sys.argv[-1]))


