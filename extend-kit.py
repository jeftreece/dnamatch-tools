#!/usr/bin/env python

# Author: Jef Treece 2019
# License: GPLv3. See accompanying LICENSE file.
# No warranty. You are responsible for your use of this program.

# Purpose:
# Extend a child's DNA kit, using both parents' kits, to improve SNP coverage.
# This program accepts raw data from AncestryDNA, 23andMe, FTDNA, MyHeritage,
# LivingDNA, and other data files that have a format similar to one of these.
# Three data files are required - one for the child and one for each parent.
# The output is a .csv file containing the combined child kit. This is not
# possible for all alleles. Only when these conditions are met does it extend
# the child's data to a new position: 1) both parents have a value at a
# location that the child does not have; 2) each parent is homozygous at that
# position.

# Instructions:
# Edit the file names below, then run this script in python2 or python3.

# Edit the location of the three data files here.
# It doesn't matter if the files are extracted or compressed.
# All data files must be based on build 37.
CHILDFILE = 'combined-me.csv'
MOTHERFILE = 'combined-mom.csv'
FATHERFILE = 'combined-dad.csv'
OUTFILE = 'extended-me.csv'

#--- adjust file names above this line, then run ---

import zipfile
import csv
import gzip
import errno
import io
import sys
import itertools

# these are used variously to indicate a no-call at the position
# in the combined kit, we omit these
NOVALUE = ('-', '--', '00', 'DD', 'II', 'I', 'D', 'DI')

# data that was read in
childkit = {}
motherkit = {}
fatherkit = {}
rsids = {}

# make sure chromosome name is presented consistently
# sometimes X results present as 'X', 'XY', '23', or '25' - always use '23'
# sometimes MT results present as '26'
# sometimes Y results present as '24'
xmap = {'X': '23', '25': '23', 'XY': '23',
        '26': 'MT',
        '24': 'Y'}
def normalize_chr(chrom):
    try:
        c = xmap[chrom]
    except KeyError:
        c = chrom
    return c

# guess the gender of the tester based on chr23 data
# if there are many heterozygous calls, the kit is probably female
# input is a dictionary, key=(chr,pos) and val=alleles
def guess_gender(kit):
    gender = 'F'
    chr23 = [kit[k] for k in kit if k[0] == '23']
    homocount = len([a for a in chr23 if len(a) == 1 or a[0] == a[1]])
    if 1.0 * homocount/len(chr23) > .95: # arbitrary magic number
        gender = 'M'
    return gender

# Read the data files
# File types currently handled:
#   .csv, .txt: plain csv file
#   .csv.gz: compressed csvfile
#   .zip: zipped csvfile
# if there is a problem with a .zip, try unzipping it before running
for ff,dd in [(CHILDFILE,childkit), (MOTHERFILE,motherkit),
                  (FATHERFILE,fatherkit)]:
    if not ff:
        print('File(s) missing - requires 3 files. Stopping.')
        sys.exit(0)
    try:
        if ff.lower().endswith('.csv.gz'):
            with gzip.open(ff, 'rt') as gf:
                lines = [l for l in gf.readlines() if not l.startswith('#')]
        elif ff.lower().endswith('.zip'):
            with zipfile.ZipFile(ff) as zf:
                for info in zf.filelist:
                    csvf = info.filename
                    if csvf.lower().endswith('.txt') or csvf.lower().endswith('.csv'):
                        break
                with zf.open(csvf) as fname:
                    textfile = io.TextIOWrapper(fname, encoding='utf8')
                    lines = [str(l) for l in textfile.readlines()
                             if not l.startswith('#')]
        elif ff.lower().endswith('.csv') or ff.lower().endswith('.txt'):
            lines = [l for l in open(ff, 'r').readlines()
                         if not l.startswith('#')]
        else:
            print('Skipping unrecognized file type: {} - use .csv, .txt, or .zip'.format(ff))
            continue
    except IOError as ioe:
        if ioe.errno == errno.ENOENT:
            print('Could not find {} - check file name and readability.'.format(ff))
            continue
        else:
            print('There may be a problem with {} - did not read it.'.format(ff))
            continue
    except TypeError:
        print('There was a problem processing {} - try unzipping it.'.format(ff))
        # raise
        continue
    except Exception as e:
        print('Error {} happened while processing {} - continuing.'.format(e,ff))
        continue

    # standardize field names and csv flavor
    # handles either rsid,chr,pos,result or rsid,chr,pos,allele1,allele2
    try:
        dialect = csv.Sniffer().sniff(''.join(lines[0:10]))
    except:
        print('{} does not appear to contain csv data - aborting'.format(ff))
        raise
    d = csv.DictReader(lines, dialect=dialect)
    ncols = len(d.fieldnames)
    if ncols not in (4,5):
        raise ValueError('unhandled type of csv file {} with fields{}'.
                             format(ff,d.fieldnames))
    fieldnames = ['rsid', 'chromosome', 'position']
    if ncols == 4:
        fieldnames.append('result')
    else:
        fieldnames += ['allele1', 'allele2']
    if d.fieldnames[0].lower().strip() == 'rsid':
        d = csv.DictReader(lines[1:], fieldnames=fieldnames, dialect=dialect)
    else:
        d = csv.DictReader(lines, fieldnames=fieldnames, dialect=dialect)

    # Process each line of the input file.
    for tup in d:
        chrom = normalize_chr(tup['chromosome'])
        if chrom == '0':
            print('Skipping {}'.format(tup))
            continue
        kv = (chrom, tup['position'])
        if ncols==5:
            result = tup['allele1']+tup['allele2']
        else:
            result = tup['result']

        # special case for FamilyFinder (ignore embedded "X" csv header)
        if result == 'RESULT':
            continue

        try:
            dd[kv] = result[0] + result[1]
        except:
            dd[kv] = result[0]
        rsids[kv] = tup['rsid']

    print('Done with {}; positions now stored: {}'.format(ff,len(dd)))
# just completed the read of all three files

# determine the gender of the child
gender = guess_gender(childkit)
print('Child appears to be {} gender'.format(gender))

# go through all values in the mother's kit to see if we can use them
for kv in motherkit:
    try:
        cv = childkit[kv]
    except:
        cv = None
    try:
        fv = fatherkit[kv]
    except:
        fv = None

    # child already has this value
    if cv and cv not in NOVALUE:
        continue

    mv = motherkit[kv]

    # continue if there's insufficient data for us to use at this position
    try:
        chrnum = int(kv[0])
        chr23 = (chrnum == 23)
    except:
        chr23 = False
    # chr23 = (kv[0] == '23')
    chrY = (kv[0] == 'Y')
    chrMT = (kv[0] == 'MT')
    chrAT = not (chr23 or chrY or chrMT)
    Female = (gender == 'F')
    if (chr23 or chrMT) and (not mv or (mv in NOVALUE)):
        continue
    elif chrY and (Female or (not fv or (fv in NOVALUE))):
        continue
    elif chrAT and (not fv or (fv in NOVALUE)):
        continue

    # mother is heterozygous - can't figure out child
    if len(mv)==2 and (2*mv[0] != mv):
        continue

    # male child got mother's chr23
    if chr23 and not Female:
        childkit[kv] = mv[0]
        continue

    # male child got father's Y value
    if chrY and not Female:
        childkit[kv] = fv[0]
        continue

    # any child got mother's MT value
    if chrMT:
        childkit[kv] = mv[0]
        continue

    # father is heterozygous - can't figure out child
    if 2*fv[0] != fv:
        continue

    # infer child from mother and father
    childkit[kv] = mv[0]+fv[0]

# sort the output by chromosome, position
chr_order = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
    '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
    'MT', 'Y']
outkeys = list(childkit)
outkeys.sort(key=lambda x:(chr_order.index(x[0]),int(x[1])))

nocalls = 0
# write the output as a .csv file
with open(OUTFILE, 'w') as csvfile:
    fieldnames = ['RSID', 'CHROMOSOME', 'POSITION', 'RESULT']
    c = csv.DictWriter(csvfile, fieldnames=fieldnames)
    c.writeheader()
    for kv in outkeys:
        if childkit[kv] not in NOVALUE:
            c.writerow({'RSID': rsids[kv], 'CHROMOSOME': kv[0],
                            'POSITION': kv[1], 'RESULT': childkit[kv]})
        else:
            nocalls += 1

# summarize
print('Child kit now {}.'.format(len(childkit)))
