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

Notes for one-time setup and other hints can be found at the bottom of
this README, under **HELP and HINTS**.


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
page of interest from your AncestryDNA matches (right click, then save
the full web page as a .html file), find the file you saved on the
computer, edit the file sniff-ancestry.py to make sure a few variables
are set correctly, and run it from the command-line. The script
requires the package "lxml" and the package "beautiful soup", so as a
one-time setup, you may need to run the commands "pip install lxml"
and "pip install beautifulsoup4"

This script takes raw web-page data that you can save from your
browser when looking at your match list, and it parses that data into
a match list that it saves in a .csv spreadsheet file. This file can
be opened with LibreOffice or any other spreadsheet that can read a
.csv file. The html file would normally look like "gobly gook" because
it's not meant to be read by a human. It's meant to be read by a web
browser. Sniff-ancestry.py turns it into something usable.

**Usage**: There are about four settings that can be modified in the script.
Check those before running.

First, bring up a match list, and scroll down to load as many matches
as you wish. Then right click on the page and "save page as..." or use
some other method to capture the page source into a file. If you have
a choice how to save, use the full web page option. It may produce a
folder with a lot of separate files and a separate .html file with the
name as you chose in saving it. Ignore the folder. You can remove it
if you want. You just need the .html file.

NOTE: you probably won't have much success trying to save all of your
matches in one go. It's recommended that you break up the list into
manageable sizes, either by filtering on a range of shared DNA or
filtering on a surname or other criteria. There may be 50,000 or more
people in the full match list, and if it works at all, it will be very
slow if you try to do it all at once.

Saving the file can typically be done by a right-click on the web
page, but the specific instructions may depend on which browser you're
using. As long as you can save it as a complete .html file, it should work.

Make sure that file matches the file name in the script, or adjust accordingly.

Next, run the script, and find the output in the .csv file it creates.

Refer to other comments in the script


## ff-matchgraph.py:

**User story**: I have match lists for a number of my relatives in
multiple spreadsheets, and I would like to generate a database and
edges and nodes from these combined matches to study matches in common
between the testers

This code is in alpha stage. It probably works as described, but refer
to comments in code, and your mileage may vary. Please provide feedback.


## cluster-segments.py:

**User story**: I have a list of segments matched for a given tester,
and I want to study which sections of each chromosome got the most
matches so I may have some additional information for chromosome
mapping.

This code produces a histogram for each chromosome. The histogram
represents how many segment matches occur at that place on the
chromosome. There are many uses for visualizing the chromosomes in
this manner. For example, it can reveal areas of the chromosomes that
are "hot" such that many matches occur at those areas.

The input segments are one or more spreadsheets as .csv files that
have, at least, a chromosome number, a starting position and an ending
position. These are the only three columns used in creating the
histograms. The .csv file may be from anywhere, as long as it contains
the three columns. For example, various segment lists can be exported
at gedmatch, or at most testing companies.

This code is in alpha stage. It probably works as described, but refer
to comments in code, and your mileage may vary. Please provide feedback.


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


## HELP and HINTS

Almost everything here will require that you have python
installed. Python is a free and open source programming language, and
it's used to run these programs. Don't be afraid! Installation is
typically very easy. It can be installed on various platforms, so it
doesn't matter if you're running Windows, Linux, or something else.
The precise installation instructions may vary a bit between different
platforms. A few tips to get you started are presented in this help
section. **Do this once** then afterwards, you will have Python
installed.

Python has been around for a long time, and there are more than one
version. Generally, you should **install version 3** (the version
number begins with 3.) if that is available to you.

Any python installation normally also installs a program called
"pip". When other software packages are needed here, the normal way to
do it is by typing the command "pip install <package>". Again, this is
a one-time step. Once you've done it, you're good to go on runnng
these programs.

**Windows** installation of Python has been covered by so
many people previously that there's no reason for us to re-invent
instructions. Watch one of these videos or tutorials, or simply use your search
engine to find your favorite installation instructions:
- https://www.tutorialspoint.com/how-to-install-python-in-windows
- https://www.youtube.com/watch?v=uDbDIhR76H4
- https://www.youtube.com/watch?v=i-MuSAwgwCU
- https://www.youtube.com/watch?v=UvcQlPZ8ecA

**Linux** installation of Python varies a bit, depending on which
distribution of Linux you are running. Use your favorite package
manager to install it, or use something along the lines of "apt
install python" if you're using command-line and a Debian-based Linux.

**MacOS** installation and validation of Python installation is covered here:
- https://www.youtube.com/watch?v=TgA4ObrowRg

**Other platforms** - no installation instructions are provided
here. You will need to find the appropriate installation instructions
for your OS by searching with a search engine, downloading the
appropriate software and following the instructions. Feel free to
provide the instructions which can be added to this readme file.

**After installing Python**

Installation of Python is done one-time, before trying to run any
programs. Along with the installation of Python, you will likely need
to install a couple of packages. Go ahead and run these commands from
a command prompt after installing python:
- pip install lxml
- pip install beautifulsoup4

**Python versions**

It's possible you have python installed already. In a command window,
type the command "python --version". If it returns with a version
number, it means you have python installed. You should also be able to
see the pip version by running the command "pip --version"

The preferred python version is any number that begins with "3.".

If you have multiple versions of python, and the default is not 3.x,
you can run specifically the correct versions of python and pip by
running the commands "python3" and "pip3". You should ensure that
these are the versions you are running for the programs here.
