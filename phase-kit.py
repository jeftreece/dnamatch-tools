#!/usr/bin/env python

# Author: Jef Treece 2019
# License: GPLv3. See accompanying LICENSE file.
# No warranty. You are responsible for your use of this program.

# Purpose:
# Separate (phase) a child's alleles into the half coming from each parent.
# This program accepts raw data from AncestryDNA, 23andMe, FTDNA, MyHeritage,
# LivingDNA, and other data files that have a format similar to one of these.
# Three data files are required - one for the child and one for each parent.
# The output is a .csv file containing the phased data and a .csv file
# containing the alleles that could not be phased.

# Instructions:
# Edit the file names below, then run this script in python2 or python3.

# Edit the location of the three data files here.
# It doesn't matter if the files are extracted or compressed.
# All data files must be based on build 37.
CHILDFILE = 'child-data.csv'
MOTHERFILE = 'mother.zip'
FATHERFILE = 'genome-father.csv.gz'
OUTFILE = 'phased-output.csv'

CHILDFILE = 'test-data/genome_Jef_Treece_v4_Full_20170201071705.zip'
CHILDFILE = 'combined-jef.csv'
MOTHERFILE = 'test-data/genome_Margaret_Treece_v5_Full_20190128080840.zip'
MOTHERFILE = 'combined-margaret.csv'
FATHERFILE = 'test-data/genome_Carl_Treece_v5_Full_20190110124151.zip'
FATHERFILE = 'combined-carl.csv'
#--- adjust file names above this line, then run ---

import zipfile
import csv
import gzip
import errno
import io
import sys
import itertools

# data that was read in
childkit = {}
motherkit = {}
fatherkit = {}
rsids = {}

# make sure chromosome name is presented consistently
# sometimes X results present as 'X', '23', or '25' - always use 'X'
# sometimes MT results present as '26'
# sometimes Y results present as '24'
xmap = {'X': '23', '25': '23',
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

# intuit the gender based on data that was read
gender = guess_gender(childkit)

outvals = {}
rejects = {}
undecided = {}
for kv in childkit:
    chrom = kv[0]
    pos = kv[1]
    try:
        mv = motherkit[kv]
    except:
        mv = None
    try:
        fv = fatherkit[kv]
    except:
        fv = None

    # if chrom=23 and male, it came from mother
    if mv and gender == 'M' and chrom == '23':
        outvals[kv] = (childkit[kv][0], '-',
                           mv.replace(childkit[kv][0], '', 1), '-')
        continue
    # Y chrom always came from father, who has nothing left to give
    elif fv and gender == 'M' and chrom == 'Y':
        outvals[kv] = ('-', childkit[kv][0], '-', '-')
        continue

    # mtDNA always inherited from mother, who has nothing left to give
    elif chrom == 'MT':
        outvals[kv] = (childkit[kv][0], '-', '-', '-')

    # normal case: both mother and father have a value at this position
    if mv and fv:
        # homozygous
        if len(childkit[kv]) == 1 or childkit[kv][0] == childkit[kv][1]:
            homo = True
            letter = childkit[kv][0]
        # father,mother or mother,father, or undecided
        else:
            homo = False
            mf = False
            fm = False
            if (childkit[kv][0] in mv) and (childkit[kv][1] in fv):
                mf = True
            if (childkit[kv][1] in mv) and (childkit[kv][0] in fv):
                fm = True
            if mf and fm:
                undecided[kv] = childkit[kv]
        if homo:
            mremainder = mv.replace(letter, '', 1)
            fremainder = fv.replace(letter, '', 1)
            if len(mremainder) != 1 or len(fremainder) != 1:
                rejects[kv] = childkit[kv]
            else:
                outvals[kv] = (letter, letter, mremainder, fremainder)
        elif mf:
            outvals[kv] = (childkit[kv][0], childkit[kv][1],
                mv.replace(childkit[kv][0], '', 1),
                fv.replace(childkit[kv][1], '', 1))
        elif fm:
            outvals[kv] = (childkit[kv][1], childkit[kv][0],
                mv.replace(childkit[kv][1], '', 1),
                fv.replace(childkit[kv][0], '', 1))
        else:
            rejects[kv] = childkit[kv]

    # didn't find result at this address in either mother or father
    else:
        # We're looking for mother or father values that only work one way for
        # the child alleles. Cartesian product gives all ways child alleles
        # could be from a parent alleles. Reduce the product to unique values,
        # then only matching values fit the bill, and if the set contains more
        # than one matching value, the result is indeterminate because the
        # allele contributed could be either one.

        if mv:
            s = set(itertools.product(childkit[kv], mv))
            choices = list(filter(lambda x:x[0]==x[1], s))
            if len(choices) == 1:
                mother_allele = choices[0][0]
                father_allele = childkit[kv].replace(mother_allele, '', 1)
                mother_un = mv.replace(mother_allele, '', 1)
                father_un = '-'
                outvals[kv] = (mother_allele, father_allele,
                                   mother_un, father_un)
                fatherkit[kv] = '--'
            else:
                rejects[kv] = childkit[kv] # can't determine from mother
        elif fv:
            s = set(itertools.product(childkit[kv], fv))
            choices = list(filter(lambda x:x[0]==x[1], s))
            if len(choices) == 1:
                father_allele = choices[0][0]
                mother_allele = childkit[kv].replace(father_allele, '', 1)
                father_un = fv.replace(father_allele, '', 1)
                mother_un = '-'
                outvals[kv] = (mother_allele, father_allele,
                                   mother_un, father_un)
                motherkit[kv] = '--'
            else:
                rejects[kv] = childkit[kv] # can't determine from father
        else:
            rejects[kv] = childkit[kv] # well we tried


print('outvals: {}, rejects: {}, undecided: {}, rsids: {}'.format(
    len(outvals), len(rejects), len(undecided), len(rsids)))

# sort the output by chromosome, position
chr_order = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
    '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
    'MT', 'Y']
outkeys = list(outvals)
outkeys.sort(key=lambda x:(chr_order.index(x[0]),int(x[1])))

# write the output as a .csv file
with open(OUTFILE, 'w') as csvfile:
    fieldnames = ['chr', 'pos', 'rsid', 'child', 'mother', 'father',
                      'mother allele', 'father allele',
                      'uninherited mother', 'uninherited father']
    c = csv.DictWriter(csvfile, fieldnames=fieldnames)
    c.writeheader()
    for k in outkeys:
        vals = outvals[k]
        mothera = fathera = '-'
        motherv = fatherv = '-'
        try:
            mothera = vals[0]
        except:
            pass
        try:
            fathera = vals[1]
        except:
            pass
        try:
            motherv = motherkit[k]
        except:
            pass
        try:
            fatherv = fatherkit[k]
        except:
            pass
        chrom = k[0]
        if (chrom == '23' and gender == 'M') or chrom == 'MT':
            fathera = '-' # didn't come from father
        else:
            try:
                fatherv = fatherkit[k]
            except:
                pass # no father alleles in data set
        if chrom == 'Y':
            fatherv = fathera = childkit[k] # father's must be child's
        elif chrom == 'MT':
            motherv = mothera = childkit[k] # child has call but mother doesn't
        else:
            motherv = motherkit[k]
        c.writerow({'child': childkit[k],
                        'chr': chrom,
                        'pos': k[1],
                        'rsid': rsids[k],
                        'mother': motherv,
                        'father': fatherv,
                        'mother allele': mothera,
                        'father allele': fathera,
                        'uninherited mother': vals[2],
                        'uninherited father': vals[3]})

# summarize the results
print('phased {:.3f} of the child alleles'.format(
    1.0*len(outvals)/len(childkit)))
