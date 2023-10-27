#!/usr/bin/env python3
# The above line helps ensure that python3 is used in this script, when running
# under Linux. You can also run it as "python <this script>" as long as your
# version of python is 3.x

# Grok the output from AncestryDNA web page to produce a match list CSV
#
# Run:
# - Check variables htmlfile and tester_csv below
# - Go to AncestryDNA match list, scroll to end of matches
# - Save page as... (same name as htmlfile below) by right-clicking
# - Run this program
# 
# Copyright 2021 Jef Treece
# Ok to use and modify for anything, but keep copyright in place
# See accompanying LICENSE file.
# Use at your own risk

# Reminder1: commented lines begin with a '#' and are ignored.

# Reminder2: when multiple lines are present, only the final one takes
# effect. For example, if you see:
a = 5
a = 6
# then the value of a is 6, the final setting.


# ===== THINGS YOU MAY WANT TO CHANGE APPEAR BELOW =====

# Here, you must specify the input file location (as saved from your web
# browser). It is the output of "save page as..." from AncestryDNA match list.
# Note: if your web browser gives you multiple options for saving the page, use
# the one that produces a complete .html file. It should be a pretty big
# file. If that doesn't work, try the other options until you find one that
# works. The file location must match where you stored the file.
#
# WINDOWS: you may need a line similar to one of these (without the hash):
#htmlfile = 'C:/Users/Treece/Desktop/A.html'
#htmlfile = 'A.html'
# OTHERS: you may need a line similar to this (without the hash):
#htmlfile = '/tmp/A.html'
htmlfile = '/tmp/A.html'

# The output file name
tester_csv = 'matches.csv'

# The separator between group names in the output csv file
group_sep = '|'

# How to handle the groups
# True: expand the groups to separate columns, "X" or "" in the column
# False: put the groups together into one column, separated by group_sep
groups_in_columns = True
groups_in_columns = False

# Whether or not to save tree information (public/private/linked/#people/thru)
disable_tree_info = True
disable_tree_info = False

# Also save "cross matches" - if it's an in-common-with report?  NB: it's not
# possible to save amount of shared cM this way. E.g. if you're logged into kit
# "A", showing matches in common with "B" and you save_crossmatches, there will
# be an entry in the spreadsheet showing that "B" matches "C" but without any
# amount for shared cM. They may not share any DNA in reality. If seeing this
# list seems useful to you, try setting it to True.
# This is experimental and may not work if set to True.
save_crossmatches = False

# "Side view" is relatively new - the prediction of which side the match occurs
# on - paternal or maternal, which may be labeled as parent1 or parent2 if no
# info is available to the matching to say which is which. This can go into the
# spreadsheet you save, and it is enabled by default. If you want to disable
# this column in the output, set this to True.
disable_sideview = False
disable_sideview = True

# ===== END. NO CHANGES ARE NORMALLY NEEDED BELOW =====


import csv, os, re, sys

try:
    import six
    # python2 will not work with this script, as likely there is no bs4 package
    # you can get to run. If you have BOTH versions 2.x and 3.x installed, just
    # make sure that you are running python3 for this script, and the bs4
    # module can be imported.
    if six.PY2:
        print('This program requires Python 3.x, and you have Python 2.x.')
        print('Correct this issue by installing Python 3, then re-run.')
        print('Refer to https://www.python.org/downloads/')
        sys.exit(1)
except:
    print('WARNING - could not determine if you are running Python 3')
    print('This code will probably not work with Python 2')
    print('Continuing anyway...')


# "pip install beautifulsoup4" may be needed (one-time setup), or in some
# installations, there may be an os package, such as "apt install python-bs4"
try:
    import lxml
    from bs4 import BeautifulSoup
except:
    print('This program requires the Beautiful Soup package.')
    print('It also requires the lxml package.')
    print('You do not appear to have one of these installed.')
    print('Command: "pip install lxml", then re-run')
    print('Command: "pip install beautifulsoup4", then re-run')
    print('Refer to https://www.pythonforbeginners.com/beautifulsoup/beautifulsoup-4-python')
    sys.exit(1)

# field names in the output .csv
fieldnames = ['Kit1', 'Name1', 'Kit2', 'Name2', 'Manager', 'Shared cM']
if not disable_sideview:
    fieldnames += ['Side',]
if not disable_tree_info:
    fieldnames += ['Tree?', 'People', 'Thruline']
fieldnames += ['Note', 'Groups', 'URL']

# helper routine takes groups column and makes it into multiple separate cols
def groups_to_cols(d, colnames):
    vals = d['Groups'].split(group_sep)
    retval = {c:'' for c in colnames if c != ''}
    for x in vals:
        if x: # an empty string does not get split and could be in the vals
            retval.update({x:'X'})
    return retval


# NB: the code is fragile, and will break if Ancestry changes page layout, HTML
# tags and variables. It should be easy to fix in most cases, since
# BeautifulSoup module does the heavy lifting. Open the raw html file and find
# the section and observe what tags are being used, then adjust below

# when color dots are used to group matches, this is the list of groups found
all_groups_found = set()

outrows = []
with open(htmlfile, 'r') as rawhtml:
    soup = BeautifulSoup(rawhtml, 'lxml')

    # page title - whose matches are these
    # in page source, this looks like <h1 ...class="pageTitle">...</h1>
    description = ' '.join([s.strip() for s in soup.find('h1').strings])

    # handle either bare matches list or matches-in-common list
    if 'DNA Matches' in description:
        r = re.compile("(.*)'s DNA Matches")
        user1 = r.match(description).groups()[0]
        id1, id2 = None, None
    else:
        card = soup.find('compare-header')
        user1 = card.find('div', {'class': re.compile('compareUserLeft ')})['title']
        user2 = card.find('div', {'class': re.compile('compareUserRight ')})['title']
        try:
            btn = card.find('div', {'class': re.compile('addEditBtn')})
            url = (btn.find('a')['href'])
            id_re = re.compile('http.*guid1=([0-9A-Z-]+).*guid2=([0-9A-Z-]+)')
            id1, id2 = id_re.match(url).groups()
        except:
            print('Unable to figure out cross-matches')
            save_crossmatches = False


    # find all matches on the entire HTML page
    # in page source, each new match begins with <match-entry ...>
    for person in soup.find_all('match-entry'):

        # get note, if there is one
        # in page source, <p class="... notesText ..."> ... </p>
        try:
            notesText = person.find('p', {'class': re.compile('notesText ')}).string.strip()
        except AttributeError:
            notesText = ''

        # get shared DNA amount in cM
        # in page source, it's a <div> with class containing "sharedDnaText"
        # shared DNA is clickable, so it's inside a <button>
        # example "27 cM | < 1% shared DNA"
        shared_cm = ''
        dna = person.find('div',{'class':re.compile('sharedDnaText')})
        button = dna.find('button')
        cms = button.string.strip().split(' ')
        if cms[1] == 'cM':
            shared_cm = cms[0].replace(',', '')

        # get match's name and unique identifier for this match
        usr = person.find('a', {'class': re.compile('userCardTitle ')})
        match_name = usr.string.strip()

        # pick up the unique identifies used by Ancestry from the URL
        # the URL is clickable by prepending https://www.ancestry.com
        match_url = usr['href']
        ids = match_url.split('/')
        # unique identifier for the comparison kit
        match_id = ids[-1]
        # unique identifier for the kit owner
        kit_id = ids[-3]

        # which groups (color dots)?
        addl = person.find('div', {'class': re.compile('additionalInfoCol groupAreaDesktopStuff')})
        groupings = addl.find_all('span', {'class': re.compile('indicatorGroup ')})
        match_groups = []
        for grp in groupings:
            match_groups.append(grp['title']) # regular groups
        starspan = addl.find('span', {'class': re.compile('iconStar ')})
        if starspan:
            match_groups.append(starspan['title']) # Starred matches
        # keep track of complete list of groups found in all matches
        all_groups_found = all_groups_found.union(set(match_groups))

        # which side? Parent1, Parent2, unassigned
        side = person.find('span', {'class': re.compile('parentLineText ')}).string.strip()
        # tweak text describing which side for spreadsheet simplicity
        if not side:
            side = 'not present'
        elif side.startswith('Parent 1'):
            side = '1'
        elif side.startswith('Parent 2'):
            side = '2'
        elif side.startswith('Maternal'):
            side = 'Maternal'
        elif side.startswith('Paternal'):
            side = 'Paternal'
        elif side.startswith('Both'):
            side = 'Both'
        else:
            # default - whatever it says
            pass

        # tree info
        try:
            # e.g. [' Public linked tree ', '2,394 People']
            tree = list(person.find('div', {'class': re.compile('areaTreeGroup ')}).strings)
            if tree[0]:
                tree_status = tree[0].strip()
            if tree[1]:
                tree_people = int(tree[1].split(' ')[0].replace(',',''))
        except:
            tree_status = ''
            tree_people = ''
        try:
            # e.g. 'Common ancestor'
            tree_ancestor = person.find('div', {'class': re.compile('iconFamily ')}).string.strip()
        except:
            tree_ancestor = ''

        
        
        # is the kit managed by someone?
        try:
            managed_by = person.find('div', {'class': re.compile('userCardSubTitle ')}).string.strip()
        except AttributeError:
            managed_by = ''

        # also save cross match (if in-common-with list)?
        if save_crossmatches and id2:
            values = [id2, user2, match_id, match_name, managed_by, '', notesText,
                group_sep.join(match_groups), match_url]
            outrows.append({fieldnames[i]:values[i] for i in range(len(fieldnames))})
            
        # save the row to be output later
        values = [kit_id, user1, match_id, match_name, managed_by, shared_cm]
        if not disable_sideview:
            values += [side,]
        if not disable_tree_info:
            values += [tree_status, tree_people, tree_ancestor]
        values += [notesText, group_sep.join(match_groups), match_url]

        outrows.append({fieldnames[i]:values[i] for i in range(len(fieldnames))})

# if requested, make the groups into a sparse table rather than single column
if groups_in_columns:
    t = []
    for r in outrows:
        gdic = groups_to_cols(r, all_groups_found)
        s = {**r, **gdic}
        s.pop('Groups')
        t.append(s)
    outrows = t
    pos = fieldnames.index('Groups')
    fieldnames = fieldnames[:pos] + list(all_groups_found) + fieldnames[pos+1:]


# save the result as a .csv
# Dialect.quotechar: is '"' by default
# Dialect.doublequote: true by default, so "Jef" becomes ""Jef""
with open(tester_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames)
    writer.writeheader()
    writer.writerows(outrows)

print('Description: {}'.format(description))
print('Saved csv file {}'.format(tester_csv))

