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
num_bins = 40

import csv, os, six, sys, functools

# python2 may not work with this script (untested), so print a warning
if six.PY2:
    print('This program is tested with Python 3.x, and you have Python 2.x.')
    print('This message is a warning; program continues to run.')
    print('Refer to https://www.python.org/downloads/')

maxes = [0,] * 23
counts = {ii:[0,] * num_bins for ii in range(23)}

# loop through input files
for fname in sys.argv[1:]:
    csvfile = open(fname)
    d = csv.DictReader(csvfile)
    segs = [(int(line['Chromosome']),
                 int(line['Start Location']),
                 int(line['End Location'])) for line in d]

    # determine maximum address for each chromosome
    for cn in range(1,23):
        try:
            mm = max([s[2] for s in segs if s[0] == cn])
            maxes[cn] = max(mm, maxes[cn])
        except ValueError:
            print('nothing for chr.{}'.format(cn))
            # pass

    # determine bin counts
    for seg in segs:
        try:
            for ii in range(int(seg[1] / (1.0 * maxes[seg[0]] / num_bins)),
                            int(seg[2] / (1.0 * maxes[seg[0]] / num_bins))):
                counts[seg[0]][ii] += 1
        except:
            print(seg, ii)

    #print(segs)
    #print(maxes)
    #print(counts)

import matplotlib.pyplot as plt

# number of suplot rows and columns
nrows = 6
ncols = 4

# list of chromosome numbers to plot
chroms = [1,5,6,8]
chroms = range(1,len(counts))

plots = [(nrows,ncols,i+1) for i in range(len(chroms))]
fig = plt.figure()

# increase height padding between subplots
fig.subplots_adjust(hspace=0.6)
for idx in range(len(chroms)):
    ax = fig.add_subplot(plots[idx][0], plots[idx][1], plots[idx][2])
    left = range(num_bins)
    height = counts[chroms[idx]]
    tick_label = ['{:,.0f}m'.format(maxes[chroms[idx]]/num_bins/1000000. * bin) for bin in range(num_bins)]
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

left = range(num_bins)
height = counts[8]
tick_label = ['{:,.0f}'.format(maxes[8]/num_bins * bin) for bin in range(num_bins)]
plt.bar(left, height, tick_label=tick_label, width=0.8)
plt.xlabel('chr 8 location')
plt.ylabel('count of matches')
plt.title('Wall matches vs chromosome 8')
plt.xticks(rotation=90)
plt.show()
