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

**User skill required**: you will need to install python, clone or copy this source code,
find your data files on the computer, edit the file combine-kits.py, and run it from the command-line.

This script accepts raw data of autosomal tests from a few different autosomal testing companies
and combines it into one.

The reason for doing this is each testing company gets a slightly different
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
