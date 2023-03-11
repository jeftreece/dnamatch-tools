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
datadir = 'tempdir_wall01a'
datadir = 'tempdir_pittmanA'
datadir = 'tempdir_pittmanAwall01a'
datadir = 'tempdir2'

# equivalent names - this should be a spreadsheet mapping kit numbers to names
# and haplogroups. The kit number should be the FTDNA kit number that is part
# of the .csv file name as saved by exporting your match list as a .csv
# file. The name should be the exact string that shows up in the match files
# for anyone matching that kit. The yhap should also be as it shows up on a
# match list. The four columns should be "kit", "name", "yhap",
# "mthap". You need one line per file in the datadir.
equivs_csv = 'kit_owners.csv'
equivs_csv = 'kit_owners_2.csv'
equivs_csv = 'kit_owners_3.csv'
equivs_csv = 'kit_owners_4.csv'

# final output file names
edgefile = 'ff-edges.csv'
nodefile = 'ff-nodes.csv'

# For creating the edge file above: shared DNA range to output: set one or both
# to None if you don't want a limit; set to a cM range if you want to only
# consider matches within that range. Does not affect database creation -
# matches outside of this range are still stored.
#example:
#cm_min = None
cm_min = 10
cm_max = 50

# Kit numbers to include in 2d array of shared DNA. For example, you could list
# kits who match each other on Y DNA and use this to see which ones of them
# share DNA with the others. Single-column csv file. The first line should be a
# label but it doesn't matter what the label is - e.g. "Id". If a kit is listed
# here that is not found in equivs_csv above, it's just ignored.
array_kits = 'y_matches.csv'
array_kits = 'y_matches2.csv'
array_kits = 'y_matches3.csv'
array_kits = 'y_matches_wall01a.csv'
array_kits = 'y_matches_pittmanA.csv'
array_kits = 'y_matches_pittmanAwall01a.csv'
array_kits = 'y_matches4.csv'

# Output file for array
array_csv = 'y_array.csv'

# The output database name. You can name it whatever you like. No need to
# change it unless you don't like the name.
sqlite_db = 'matches.db'
sqlite_db = 'matches2.db'
sqlite_db = 'matches3.db'

# If database is already built, you can set this to False
build_db = False
build_db = True

# rejected typically because duplicate id within same match file
# not used - rejects stored in the database
# rejects_file = 'rejects.out'

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

# return True if file1 is newer than file2 in the root directory
def newer(rootdir, f1, f2):
    if os.path.getmtime(os.path.join(rootdir,f1)) > os.path.getmtime(os.path.join(rootdir,f2)):
        print(f1, 'is newer than', f2)
        return True
    return False

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
                    source integer references people(rowid),
                    target integer references people(rowid),
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
    try:
        curs.execute('drop table namecounts')
    except:
        pass
    curs.execute('''create table namecounts(
                    tester integer references people(rowid),
                    matched integer references people(rowid),
                    namecount integer)''')

    try:
        curs.execute('drop table rejects')
    except:
        pass
    curs.execute('''create table rejects(
                    tester integer references people(rowid),
                    matched integer references people(rowid),
                    rejectcount integer)''')
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
                                person['yhap'], person['mthap']))
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

# try to handle every file found in the datadir, only keeping newest
owner_files = {}
for root, dirs, files in os.walk(datadir):
    for candidate in files:
        owner = fname_re.match(candidate).groups()[0]
        if owner in owner_files:
            # file for this owner already stored
            fname = owner_files[owner]
            if newer(root,candidate,fname):
                # found a newer file for this owner
                owner_files[owner] = candidate
        else:
            # first file found for this candidate
            owner_files[owner] = candidate

# a list of the newest file for each tester
in_files = [(root, owner_files[ff]) for ff in owner_files]

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
            people = set()
            rejects = set()
            names = {}
            for match in matches:
                name = normalize_name(match['Full Name'])
                shared_dna = match['Shared DNA']
                yhap = match['Y-DNA Haplogroup']
                mthap = match['mtDNA Haplogroup']

                # person "unique" identifier: name, yhap, mthap
                personID = (name,yhap,mthap)
                try:
                    curs.execute('''insert into people(name,yhap,mthap)
                                 values(?,?,?)''', personID)
                    pid = curs.lastrowid
                except sqlite3.IntegrityError:
                    curs.execute('''select rowid from people
                                  where name=? and yhap=? and mthap=?''',
                                     personID)
                    pid = curs.fetchone()[0]
                if not pid:
                    print('Failed to store match: {} and {}'.format(owner_name,
                                                                        name))
                    continue

                # count number of times a given name occurs within matches
                if pid in names:
                    names[pid] += 1
                else:
                    names[pid] = 1

                # did we already encounter match with same name and haplo?
                if names[pid] > 1:
                    rejects.add(pid)
                    # print('rejecting duplicate person', personID)
                    continue

                # remember that we processed someone with this ID already
                people.add(pid)

                # source,target sorted so there are no duplicates stored
                # any graph of these nodes is not directed
                edges = sorted([owner_id, pid])
                tuples.append((edges[0], edges[1], shared_dna))

            if names:
                curs.executemany('insert into namecounts values(?,?,?)',
                                [((owner_id,) + tt) for tt in names.items()])

            # TBD: insert actual count rather than 1
            if rejects:
                curs.executemany('insert into rejects values(?,?,?)',
                                [((owner_id, pp, 1)) for pp in rejects])

            if tuples:
                curs.executemany('insert or ignore into edges values(?,?,?)',
                                 tuples)
            db.commit()

    except:
        print('Did not process file {}'.format(fname))
        raise

if False:
    with open(rejects_file, 'w') as fp:
        for thingy in rejects:
            fp.write(repr(thingy)+'\n')
    

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
