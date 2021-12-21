# dnamatch-tools

Open-source tools providing capabilities for your DNA data from various DNA testing companies.

This project provides simple tools for working with various raw DNA and match list files for genetic genealogy.

Goals:
- open source license to promote sharing
- not dependent on a particular OS or platform
- community contributions accepted so it's not necessary to fork other projects
- provides capabilities that enhance or extend DNA matching

The typical user is expected to be able to find and install python, run run python from the command-line,
and locate and manipulate text files on the computer.

## combine-kits.py:

**User story**: as a genetic genalogist who has tested at AncestryDNA, 23andMe and FTDNA,
I want to combine all of my data into a single data file that has the best coverage
possible from the available data for better matching and SNP overlap.

**User story**: as a tester at another company, I want to upload my data file to gedmatch,
but it's being rejected by gedmatch due to formatting or ordering or something.

**User skill required**: you will need to install python, clone or copy this source code,
find your data files on the computer, edit the file combine-kits.py, and run it from the command-line.

This script accepts raw data of autosomal tests from a few different autosomal testing companies
and combines it into one.

Another way to run it is with one kit instead of multiple ones.
By running it with just one test, certain problems may be fixed in the data.
In at least one case, the FTDNA data file could not be uploaded, but after
running this program, the output file uploaded OK. The main thing it "fixed"
was the chromosome ordering within the file.

The reason for combining kits is each testing company gets a slightly different
coverage of the DNA, which may also depend on when you tested,
since occasionally testing companies switch to different testing technology.

Comparing your results with someone else from the same testing company,
using the same testing technology, will not be improved significantly by combining test results.
However, comparing your results with someone who tested at a different company or whose results
came from a different testing technology, will likely be improved because there will be more
SNPs that can be compared.
The end result may mean more-relevant matches and better definition of the end-points
of the overlapping DNA segments.

To use the combined file, it can be read into a spreadsheet, manipulated as text other ways, or uploaded
to a DNA match service such as gedmatch.

**Usage**: refer to comments in the script

## phase-kit.py:

**User story**: I have autosomal DNA results for both of my parents, and
I want to determine which allele came from which parent so I can do more-precise
matching and mapping.

**User skill required**: you will need to install python, clone or copy this source code,
find your data files on the computer, edit the file phase-kit.py, and run it from the command-line.

This script accepts raw data of autosomal tests from a few different autosomal testing companies. The files may be compressed (.zip or .csv.gz) or uncompressed.
It currently requires a child, mother and father data and does not yet try
to phase if only one parent is available.

The data files may also be combined kits, produced by combine-kits.py.

For a given location to be phased, both parents must have values at that location. Locations that are missing a parent's data are rejected and not written to the output. Uncertain locations (where it's impossible to determine which parent contributed which allele) are also rejected.

The output is a .csv to be read into a spreadsheet.

**Usage**: refer to comments in the script


## extend-kit.py:

**User story**: I have autosomal DNA results for me and both of my parents, and
I want to utilize their data to fill in new positions in my own kit
to make my kit better for matching.

**User skill required**: you will need to install python, clone or copy this source code,
find your data files on the computer, edit the file extend-kit.py, and run it from the command-line.

This script accepts raw data of autosomal tests from a few different autosomal testing companies. The files may be compressed (.zip or .csv.gz) or uncompressed.
It currently requires a child, mother and father data.

The data files may also be combined kits, produced by combine-kits.py.

For an allele at a given location of a chromosome to be deduced for the child, both parents must have values at that location, and both parents must be homozygous at that location. The output consists of the union of the original positions the child had and the additional values that can be determined from the parents.

The output is a .csv to be read into a spreadsheet or uploaded to a matching service such as gedmatch.

**Usage**: refer to comments in the script


## sniff-ancestry.py:

**User story**: As a genealogist using DNA matches, I would like a
list of my matches from AncestryDNA in a spreadsheet so I can keep
better track, history and notes.

**User story**: I have AncestryDNA matches that I want to pull out
into a spreadsheet for match and network analysis with graphviz,
gephi and other tools, yet I don't see any way to do that from the
web page platform. Help!

**User story**: I have seen some spreadsheet methods that use
cut-and-paste of AncestryDNA matches into a spreadsheet with macros
and formulas, but I would like a programmatic way of generating my
spreadsheet that I can understand.

**User skill required**: you will need to install python, clone or
copy this source code, log into your AncestryDNA account, save the web
page of interest from your AncestryDNA matches (right click...), find
the file you saved on the computer, edit the file sniff-ancestry.py to
make sure a few variables are set correctly, and run it from the
command-line.

This script takes raw web-page data that you can save from your
browser when looking at your match list, and it parses that data into
a match list that it saves in a .csv spreadsheet file. This file can
be opened with LibreOffice or any other spreadsheet that can read a
.csv file. The file would normally look like "gobly gook" because it's
not meant to be read by a human. It's meant to be read by a web
browser.

**Usage**: There are about four settings that can be modified in the script.
Check those before running.

First, bring up a match list, and scroll down to load as many matches
as you wish. Then right click on the page and "save page as..." or use
some other method to capture the page source into a file.

Make sure that file matches the file name in the script, or adjust accordingly.

Next, run the script, and find the output in the .csv file it creates.

Refer to other comments in the script


## merge-csv.py:

**User story**: I've pulled a bunch of DNA matches into multiple
spreadsheets, and I would like to combine those spreadsheets into one
file, with duplicates removed so I can use the de-duplicated rows as
input into another program.

**User skill required**: you will need to install python, clone or
copy this source code, and run it as a python program

This script takes multiple .csv files and combines them into one file
that has duplicate rows removed.  Each .csv file must have identical
columns for the merge to take place. Non-identical .csv files are
ignored.

**Usage**: There are no settings. Run the program with all of the file
names you want to merge, plus the output file (final filename) on the
command line.

Example: merge-csv.py a.csv b.csv c.csv out.csv
