#!/usr/bin/env python

# Author: Jef Treece 2019
# License: GPLv3. See accompanying LICENSE file.
# No warranty. You are responsible for your use of this program.

# Purpose:
# Combine raw data files from multiple autosomal tests into one file.  The
# combined file may have better coverage than the individual files.  Currently
# handles AncestryDNA, 23andMe and FTDNA, MyHeritage, and LivingDNA.
# It may support others not yet tested.  The resulting file can be uploaded
# to gedmatch.

# Instructions:
# Edit the file names below, then run this script in python2 or python3.

# Edit the data files to be combined.
# There should be at least two files listed.
# It doesn't matter if the files are extracted or compressed.
# In the examples given below, lines starting with '#' are ignored,
# and these examples are for files residing in a folder called 'test-data'.
# All data files must be based on build 37.
INFILES = [
  'test-data/37_C_Treece_Chrom_Autoso_20170722.csv.gz',
  'test-data/genome_Carl_Treece_v5_Full_20190110124151.zip',
  'test-data/CarlTreece-AncestryDNA-dna-data-2017-12-13.zip',
#  'test-data/MyHeritage_raw_dna_data.zip',
#  'test-data/no-data.csv', # fails, empty file
#  'test-data/unreadable.csv', # fails, no file permissions
#  'test-data/badname.csv', # fails, file does not exist
#  'test-data/CarlTreece-AncestryDNA-dna-data-2017-12-13', # fails - no file extension
#  'test-data/genome_Carl_Treece_v5_Full_20190110124151.txt', # ok - already unzipped
#  '../FamilyFinder/37_J_Treece_Chrom_Autoso_20170722.csv.gz',
#  '../23andMe/genome_J_Treece_v4_Full_20171213100231.zip',
#  '../AncestryDNA/JTreece-AncestryDNA-dna-data-2017-12-13.zip',
  ]
OUTFILE = 'combined-output.csv'

#--- adjust file names above this line, then run ---

import zipfile
import csv
import gzip
import errno
import io

# resulting mash-up
geno = {}

# Put the 2-char allele pair in deterministic order.
# e.g., the combined output considers "GT" equivalent to "TG"
def normalize_result(result):
    if len(result) == 1:
        return result
    if len(result) != 2:
        print('BAD RESULT: {}'.format(result))
    if result[0] > result[1]:
        result = result[1] + result[0]
    return result

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

    
# Take calls from multiple results and unify if possible.
# E.g. if one company reports "--" and another company reports "GT" use "GT"
# Handles most instances but might miss some fixable inconsistencies.
# Input is a set of calls, one for each testing company, for a given position.
def normalize_calls(s):
    arr = list(s)
    rsid = arr[0][0]    # RSID names may vary; pick any one RSID name
    results = [r[1] for r in arr]
    if '--' in results:
        results.remove('--')
    if '00' in results:
        results.remove('00')
    results.sort()      # 'A' sorts before 'AA'
    try:
        if results[0] * 2 == results[1]:
            results = results[1:]
    except:
        pass # maybe already reduced

    # after the above reductions, there's only one distinct value remaining
    if results and results == [results[0]] * len(results):
        return set( [(rsid,results[0])] )
    return s # fail to unify results

# Loop through data files:
# To support additional company data files, this loop may need to be tweaked.
# File types currently handled:
#   .csv, .txt: plain csv file
#   .csv.gz: compressed csvfile
#   .zip: zipped csvfile
# Companies supported: AncestryDNA, FTDNA, 23andMe
# Additional companies might work, if data format is similar.
for f in INFILES:
    if not f:
        continue
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
            print('Skipping unrecognized file type: {} - use .csv, .txt, or .zip'.format(f))
            continue
    except IOError as ioe:
        if ioe.errno == errno.ENOENT:
            print('Could not find {} - check file name and readability.'.format(f))
            continue
        else:
            print('There may be a problem with {} - did not read it.'.format(f))
            continue
    except TypeError:
        print('There was a problem processing {} - try unzipping it.'.format(f))
        # raise
        continue
    except Exception as e:
        print('Error {} happened while processing {} - continuing.'.format(e,f))
        continue

    # standardize field names and csv flavor
    # handles either rsid,chr,pos,result or rsid,chr,pos,allele1,allele2
    try:
        dialect = csv.Sniffer().sniff(''.join(lines[0:10]))
    except:
        print('{} does not appear to contain csv data - skipping'.format(f))
        continue
    d = csv.DictReader(lines, dialect=dialect)
    ncols = len(d.fieldnames)
    if ncols not in (4,5):
        raise ValueError('unhandled type of csv file {} with fields{}'.
                             format(f,d.fieldnames))
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

    # At each position discovered, add to the set of reads at that same
    # position. Later, after all files are read, try to reduce the set down to
    # one read at that position.

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

        # put logically equivalent results into a deterministic result
        # output will not be phased, no matter whether input was or not
        result = normalize_result(result)

        vv = (tup['rsid'], result)
        try:
            geno[kv].append(vv)
        except:
            geno[kv] = [vv,]
    print('Done with {}; positions now stored: {}'.format(f,len(geno)))


# Handle the positions that have more than one value.
# This happens when more than one DNA kit has a call for the same position.
# The different kits might have different values at those positions.
mults = 0
ones = 1
outvals = []
for g in geno:
    # get rid of duplicates
    s = set(geno[g])
    # apply some rules to fix logically equivalent calls
    s = normalize_calls(s)
    # if there are still multiple calls, we will not write them to output
    if len(s) > 1:
        mults += 1
        # uncomment if you want to see discarded calls
        # print(g, s)

    # everything is fine with this position, so write it to the output
    elif len(s) == 1:
        ones += 1
        outvals.append((list(s)[0][0], g[0], g[1], list(s)[0][1])) # r,c,p,v
        # print(g, s)

# sort the output by chromosome, position
chr_order = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
    '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
    'MT', 'Y']
outvals.sort(key=lambda x:(chr_order.index(x[1]),int(x[2])))

# write the output as a .csv file
with open(OUTFILE, 'w') as csvfile:
    fieldnames = ['RSID', 'CHROMOSOME', 'POSITION', 'RESULT']
    c = csv.DictWriter(csvfile, fieldnames=fieldnames)
    c.writeheader()
    for r in outvals:
        c.writerow({'RSID': r[0], 'CHROMOSOME': r[1],
                        'POSITION': r[2], 'RESULT': r[3]})

# summarize the results
print('Inconsistent calls not written: {}\nCombined calls: {}'.
          format(mults,ones))
