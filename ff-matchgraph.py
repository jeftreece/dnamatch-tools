#!/usr/bin/env python3
# The above line helps ensure that python3 is used in this script, when running
# under Linux. You can also run it as "python <this script>" as long as your
# version of python is 3.x

# Purpose:
# Process the output from a group of FamilyFinder match lists to produce .csv
# files for nodes and edges that can be used as input to gephi et al.
#
# THIS PROGRAM WORKS BUT NOT YET FINISHED - "alpha"
# IT MAY CHANGE SIGNIFICANTLY
#
# Run:
# - Check variables below
# - Save Family Finder match list(s) as .csv file(s) in a folder
# - For example, use the match list for yourself and a few cousins
# - Run this program
# - The two output .csv files can be used as gephi input
# 
# Copyright 2022 Jef Treece
# Ok to use and modify for anything, but keep copyright in place
# See accompanying LICENSE file.
# Use at your own risk

import hashlib, csv, sqlite3, re, os



# --- Things you may want to change ---

# The name of the folder containing .csv files from Family Finder
# matches. Every .csv file in this directory will be attempted.  We refer to a
# folder containing match lists as a "project". This could be an actual
# project, such as a surname project and all of the match lists downloaded from
# that surname project, or it could just be your own collection of match lists:
# e.g., match lists for all of the kits you manage.
datadir = 'match-ff-data'
datadir = 'tempdir'

# equivalent names - this should be a spreadsheet mapping kit numbers to names
# and haplogroups. The kit number should be the FTDNA kit number that is part
# of the .csv file name as saved by exporting your match list as a .csv
# file. The name should be the exact string that shows up in the match files
# for anyone matching that kit. The y-haplo should also be as it shows up on a
# match list. The four columns should be "kit", "name", "y-haplo",
# "mt-haplo". You need one line per file in the datadir.
equivs_csv = 'kit_owners.csv'
equivs_csv = 'kit_owners_2.csv'

# final output file names
edgefile = 'ff-edges.csv'
nodefile = 'ff-nodes.csv'

# shared DNA range to output: set one or both to None if you don't want a
# limit; set to a cM range if you want to only consider matches within that
# range.
#example:
#cm_min = None
cm_min = 12
cm_max = 40

# Kit numbers to include in 2d array of shared DNA. For example, you could list
# kits who match each other on Y DNA and use this to see which ones of them
# share DNA with the others. Single-column csv file. The first line should be a
# label but it doesn't matter what the label is - e.g. "Id". If a kit is listed
# here that is not found in equivs_csv above, it's just ignored.
array_kits = 'y_matches.csv'
array_kits = 'y_matches2.csv'
array_kits = 'y_matches3.csv'

# Output file for array
array_csv = 'y_array.csv'

# The output database name. You can name it whatever you like. No need to
# change it unless you don't like the name.
sqlite_db = 'matches.db'

# If database is already built, you can set this to False
build_db = False
build_db = True


# --- Usually, no changes are needed below this line ---

# Procedure: md5
# Purpose: return a md5 hash of a given object as a string signature
def md5(obj):
    md5hash = hashlib.md5()
    md5hash.update(str(obj).encode('utf-8'))
    return md5hash.hexdigest()

# Procedure: normalize_name
# Purpose: "fix" issues in name - at present, a name may show up with extra
# spaces in match files that are not present in Project Participants file. This
# happens if the user enters space(s) before or after first, middle or last
# name. Thus, here we need to treat "Jef  Treece" the same as "Jef Treece"
#
# NB: FTDNA should present full name the same way in Project Information as
# they do in match lists, and we would not have to do this.
def normalize_name(fullname):
    return re.sub(r'( )\1+', r'\1', fullname)

# Create the database file for storing results
# NB: these are used internally and don't need to be directly accessed
db = sqlite3.connect(sqlite_db)
curs = db.cursor()
if build_db:
    try:
        curs.execute('drop table edges')
    except:
        pass
    curs.execute('''create table edges (
                    source char references people(rowid),
                    target char references people(rowid),
                    cm float,
                    unique(source, target))''')
    try:
        curs.execute('drop table people')
    except:
        pass
    curs.execute('''create table people (
                    name char,
                    kit char default NULL,
                    yhap char,
                    mthap char,
                    unique(kit),
                    unique(name,yhap,mthap))''')
    db.commit()

# FTDNA does not give us a unique identifier for a match. This creates a severe
# problem. Two distinct people may have an identical full name. Any match in a
# matches list might correspond to a project member, so we need to be able to
# make the association between the kit owner and a match in someone else's
# match list.
#
# In the match lists, we need to try to use the available information to see if
# we can figure out the identity of the named match. The readily available
# information in the match list is full name and both haplogroups, either of
# which may be null. This is not enough information to be certain, but it's
# better than using just the full name.
#
# One problem is that the haplogroup information can change. For example, if
# the tester takes Big-Y, the Y haplogroup could be refined and not be the same
# thing it was yesterday. If match lists were downloaded yesterday and the
# kit_owners file were prepared today, the entries would differ when they
# should not. There is no known solution to this problem.
#
# Another problem is the fact that a person could have the same name AND
# haplogroup as some other tester. There is no known solution to this problem,
# given what information FTDNA gives us in the match list.
#
# Another problem is that the haplogroup information is not reported in the
# project participants spreadsheet - it's a manual process to prepare this
# spreadsheet, and updating it will require your time. There is no way to find
# out if haplogroups changed, apart from manual inspection.
#
# Another problem is that users can change their name. Any reports or analysis
# may reflect the "wrong" name if the tester changed their name since the
# program ran (e.g. corrected a spelling error or got married and changed their
# surname or changed "TBD TBD" to an actual name).
#
# The compromise partial-solution to the uniqueness problem is list the name
# and haplogroup information in the kit_owner file, and make sure that it
# corresponds to what is presented in the match lists, which basically means
# create the kit_owner file at the same time the match lists are downloaded and
# manually edited and reviewed for correctness.
#
# A md5 hash is used to see if two named people in the match list appear to be
# identical to each other. If the name is identical and the haplogroups are
# identical, the md5hash will be identical. So the credentials in kit_owners
# must match exactly the corresponding entry in a match list.
#
# It is assumed that a match occurs only once in a matches file, so if two or
# more indistinguishable matches are found in the same file, it triggers an
# error, and kicks matches out to a "rejects" file.
#
# Keep in mind, this is not foolproof, so some matches could be off.


# open the equivs file to find names associated with kit numbers of the input
# files. If there is no row in this file matching the kit number, the input
# file will not be processed.
kit_ids = {}
with open (equivs_csv, 'r', encoding='utf-8-sig') as csvfile:
    equivs = csv.DictReader(csvfile)
    for person in equivs:
        try:
            if build_db:
                curs.execute('''insert into people(name,kit,yhap,mthap)
                           values(?,?,?,?)''',
                            (person['name'], person['kit'],
                                person['y-haplo'], person['mt-haplo']))
                pid = curs.lastrowid
            else:
                curs.execute('select rowid from people where name=?',
                             (person['name'],))
                pid = curs.fetchone()[0]
        except sqlite3.IntegrityError:
            print('Failed to store {} because they appear twice in {}'.format(
                person['name'], equivs_csv))
            curs.execute('select rowid from people where name=?',
                             (person['name'],))
            pid = curs.fetchone()[0]
            
        kit_ids[person['kit']] = (pid, person['name'])
db.commit()


# process the match files found in datadir...

# regular expression to determine the kit number from the file name 
fname_re = re.compile(r'([\w]{3,10})_', re.I)

# try to handle every file found in the datadir
in_files = []
for root, dirs, files in os.walk(datadir):
    for fname in files:
        in_files.append((root,fname))

# walk through all of the files
for dirname,fname in in_files:
    if not build_db:
        continue
    try:
        owner='?'
        fpath = os.path.join(dirname, fname)
        owner = fname_re.match(fname).groups()[0]
        owner_id, owner_name = kit_ids[owner]
    except:
        print('Not processing {} because owner {} is not in {}'.format(
            fname, owner, equivs_csv))
        continue
    try:
        # process lines (matches) in the file
        print('Reading matches from {}...'.format(fpath))
        with open (fpath, 'r', encoding='utf-8-sig') as csvfile:
            matches = csv.DictReader(csvfile)
            tuples = []
            nodes = []
            for match in matches:
                name = normalize_name(match['Full Name'])
                shared_dna = match['Shared DNA']
                yhap = match['Y-DNA Haplogroup']
                mthap = match['mtDNA Haplogroup']
                pid = None
                try:
                    curs.execute('''insert into people(name,yhap,mthap)
                                 values(?,?,?)''', (name,yhap,mthap))
                    pid = curs.lastrowid
                except sqlite3.IntegrityError:
                    curs.execute('''select rowid from people
                                  where name=? and yhap=? and mthap=?''',
                                     (name,yhap,mthap))
                    pid = curs.fetchone()[0]
                if not pid:
                    print('Failed to store match: {} and {}'.format(owner_name,
                                                                        name))
                    continue
                # source,target sorted so there are no duplicates stored
                # this strategy means graph is not directed
                edges = sorted([owner_id, pid])
                tuples.append((edges[0], edges[1], shared_dna))
            curs.executemany('insert or ignore into edges values(?,?,?)',
                                 tuples)
            db.commit()

    except:
        print('Did not process file {}'.format(fname))
        raise


# only output edges within range of cM specified
if cm_min and cm_max:
    cm_range = 'where cm between {} and {}'.format(cm_min, cm_max)
elif cm_min:
    cm_range = 'where cm > {}'.format(cm_min)
elif cm_max:
    cm_range = 'where cm < {}'.format(cm_max)
else:
    cm_range = ''

# write the two .csv files
curs = curs.execute('select source, target, cm from edges {}'.format(cm_range))
with open(edgefile, 'w', newline='') as csvfile:
    edgecsv = csv.writer(csvfile)
    edgecsv.writerow(['Source', 'Target', 'weight'])
    for c in curs:
        edgecsv.writerow(c)

curs = curs.execute('''select rowid, name, kit from people where
   rowid in (select source from edges {} union
          select target from edges {})'''.format(cm_range, cm_range))
with open(nodefile, 'w', newline='') as csvfile:
    nodecsv = csv.writer(csvfile)
    nodecsv.writerow(['Id', 'label', 'kit'])
    for c in curs:
        nodecsv.writerow(c)


# walk through array_kits file and output shared cM array
kitlist = []
with open (array_kits, 'r', encoding='utf-8-sig') as csvfile:
    kitcsv = csv.DictReader(csvfile)
    kitfield = kitcsv.fieldnames[0]
    print(kitfield)
    for person in kitcsv:
        if person[kitfield] not in kit_ids:
            print('not found: {}'.format(person[kitfield]))
        else:
            kitlist.append(person[kitfield])
    print(kitlist)
    sq = 'select rowid from people where kit=?'
    kitids = [curs.execute(sq,(kk,)).fetchone()[0] for kk in kitlist]
    print(kitids)
    fieldnames = ','.join(['X'] + kitlist)
    print(fieldnames)
    outrows = []
    for k1 in kitids:
        rr = [kitlist[kitids.index(k1)]]
        for k2 in kitids:
            if k1 == k2:
                rr.append('X')
                continue
            curs.execute('''select cm from edges e
                            where e.source=? and e.target=?
                            or e.source=? and e.target=?''',
                            (k1, k2, k2, k1))
            cm = curs.fetchone()
            if cm:
                rr.append(cm[0])
            else:
                rr.append('')
        outrows.append(rr)
        print(rr)

print('writing...')
with open(array_csv, 'w', newline='') as csvfile:
    arrcsv = csv.writer(csvfile)
    arrcsv.writerow(['X'] + kitlist)
    for rr in outrows:
        arrcsv.writerow(rr)

db.commit()
