#!/usr/bin/env python3
# The above line helps ensure that python3 is used in this script, when running
# under Linux. You can also run it as "python <this script>"

# Python3 is recommended, but it may run under python2

# Author: Jef Treece 2022
# License: GPLv3. See accompanying LICENSE file.
# No warranty. You are responsible for your use of this program.

# Purpose:
# Form histogram clusters of matching segments "hot spots"
#
# For example, if you use a list of known segments matching some related
# testers who share a common ancestor, you might expect to find certain areas
# of certain chromosomes more likely to be involved in the match.
#
# Segment files must be .csv files with Chromosome, Start Location, and End
# Location columns
#
# Run:
# - check variables in section below and run with segment files
#

# number of bins on each chromosome for histograms
num_bins = 50

# graph range for each chromosome
# False: graph entire chromosome
# True: graph only up to the largest matching segment
actual_max = True
actual_max = False

# number of chromosomes
nchrom = 23

# plot all chromosomes by default, but list can be overriden as in example here
# chroms = [1,5,6,8]
chroms = range(1,nchrom)


#----- most tuning and editing is above this line -----

# input .csv file must match one of these signatures (column names)
csv_signatures = {
    '23andMe': ('Chromosome Number', 'Chromosome Start Point',
                    'Chromosome End Point'),
    'FamilyFinder1': ('Chromosome', 'Start Location', 'End Location'),
    'FamilyFinder2': ('Chromosome', 'Start Position', 'End Position'),
    'Gedmatch1': ('Chr', 'Start', 'End'),
    'Gedmatch2': ('Chr', 'Start Position', 'End Position'),
    'Gedmatch3': ('Chr', 'B37 Start', 'B37 End'),
    }

# len of each chromosome, from various sources - may not be exactly
# correct for current reference genome. Only affects histogram graph range.
chr_maxes = {
    '1': 249250621,
    '2': 243199373,
    '3': 199501827,
    '4': 191273063,
    '5': 180915260,
    '6': 171115067,
    '7': 159138663,
    '8': 146364022,
    '9': 141213431,
    '10': 135374737,
    '11': 135006516,
    '12': 133851895,
    '13': 115169878,
    '14': 107349540,
    '15': 102531392,
    '16': 90354753,
    '17': 81195210,
    '18': 78077248,
    '19': 63811651,
    '20': 63025520,
    '21': 48129895,
    '22': 51304566,
    'X': 155270560,
    'Y': 59373566
    }

import csv, os, six, sys, functools

# test if this is a known format .csv and return the header names
def match_signature(fieldnames, signatures):
    for signature in signatures:
        if signatures[signature][0] in fieldnames and \
                 signatures[signature][1] in fieldnames and \
                 signatures[signature][2] in fieldnames:
            return signatures[signature]
    return None

# python2 may not work with this script (untested), so print a warning
if six.PY2:
    print('This program is tested with Python 3.x, and you have Python 2.x.')
    print('This message is a warning; program continues to run.')
    print('Refer to https://www.python.org/downloads/')

# graph either actual max discovered among matches or use chromosome length
maxes = {}
if actual_max:
    # loop through input files
    for fname in sys.argv[1:]:
        csvfile = open(fname)
        d = csv.DictReader(csvfile)
        csv_cols = match_signature(d.fieldnames, csv_signatures)
        if not csv_cols:
            print('Input .csv file does not match a known format. Exiting.')
            sys.exit(1)

        segs = [(line[csv_cols[0]], int(line[csv_cols[1]]),
                     int(line[csv_cols[2]]))
                for line in d]

        # determine maximum address for each chromosome
        for cn in range(1,nchrom):
            try:
                mm = max([s[2] for s in segs if s[0] == cn])
                try:
                    maxes[cn] = max(mm, maxes[cn])
                except KeyError:
                    maxes[cn] = mm
            except ValueError:
                #print('nothing for chr.{}'.format(cn))
                pass
else:
    maxes = chr_maxes


# keeping track of number of matches for each chromosome section
counts = {ii:[0,] * num_bins for ii in maxes}

# loop through input files, count each segment where it lands
for fname in sys.argv[1:]:
    csvfile = open(fname)
    d = csv.DictReader(csvfile)
    csv_cols = match_signature(d.fieldnames, csv_signatures)
    # print('relevant columns:', csv_cols)
    segs = [(line[csv_cols[0]], int(line[csv_cols[1]]),
                 int(line[csv_cols[2]]))
                for line in d if line[csv_cols[0]]]

    # bin counts - bump if any part of matching segment is in bin range
    for seg in segs:
        binsize = 1.0 * maxes[seg[0]] / num_bins
        try:
            for ib in range(0,num_bins):
                endpoint1 = ib * binsize
                endpoint2 = (ib+1) * binsize
                if seg[1] < endpoint2 and seg[2] >= endpoint1:
                    counts[seg[0]][ib] += 1
        except:
            print(seg, ib)
            raise

# uncomment if you're a nerd and want to see inner workings
#print(segs)
#print(maxes)
#print(counts['1'])

# ----- code below produces the actual graph, using matplotlib.pyplot -----

import matplotlib.pyplot as plt

# number of suplot rows and columns
nrows = 6
ncols = 4

# produce a sub-plot for each chromosome number in chroms list
plots = [(nrows,ncols,i+1) for i in range(len(chroms))]
fig = plt.figure()

# increase height padding between subplots
fig.subplots_adjust(hspace=0.6)

for chrom in maxes:
    # skip X and Y for now - only handle 1 through 22
    if chrom in ('X', 'Y'):
        continue
    # print('Chromosome', chrom, '...')
    idx = int(chrom) - 1
    ax = fig.add_subplot(plots[idx][0], plots[idx][1], plots[idx][2])
    left = range(num_bins)
    try:
        height = counts[chrom]
    except KeyError:
        height = [0,] * num_bins
    tick_label = ['{:,.0f}m'.format(maxes[chrom]/num_bins/1000000. * bin) for bin in range(num_bins)]

    ax.bar(left, height, tick_label=tick_label, width=0.8)
    #ax.set_xticklabels(tick_label)
    ax.tick_params(labelrotation=90,labelsize=7)
    #ax.set_title('chr.{}'.format(chroms[idx]))
    ax.set_xlabel('chr.{}'.format(chroms[idx]))
    ax.set_ymargin(.2)

fig.suptitle('Histogram of segments matched for {}'.format(sys.argv[1]))
fig.supylabel('match counts on region')

plt.show()
    

sys.exit(0)



# ----- code below is currently unused -----

left = range(num_bins)
height = counts[8]
tick_label = ['{:,.0f}'.format(maxes['8']/num_bins * bin) for bin in range(num_bins)]
plt.bar(left, height, tick_label=tick_label, width=0.8)
plt.xlabel('chr 8 location')
plt.ylabel('count of matches')
plt.title('Wall matches vs chromosome 8')
plt.xticks(rotation=90)
plt.show()
