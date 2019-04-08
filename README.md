# dnamatch-tools

Open-source tools providing capabilities for your DNA data from various DNA testing companies.

This project provides simple tools for working with various raw DNA files for genetic genealogy.

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

For a given location to be deduced for the child, both parents must have values at that location, and both parents must be homozygous at that location. The output consists of the union of the original positions the child had and the additional values that can be determined from the parents.

The output is a .csv to be read into a spreadsheet or uploaded to a matching service such as gedmatch.

**Usage**: refer to comments in the script
