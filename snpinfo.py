#!/usr/bin/env python3
"""
  Purpose:
    report info about any Y SNP

  Usage:
    -s <snp>  show information about a snp by name or position

  Copyright:
    For free distribution under the terms of the
    GNU General Public License, version 3 (29 June 2007)
    https://www.gnu.org/licenses/gpl.html

  Jef Treece, 29 Dec 2023
"""

import sqlite3, sys, time, argparse, pysam

config = {}
# affects diagnostic messages, which go to stderr
config['verbosity'] = 1
config['db_file'] = 'variants.db'
# SNP definitions, hg38, from http://ybrowse.org/gbrowse2/gff/ for example
config['hg38_snp_file'] = '/home/treece/Download/snps_hg38.vcf.gz'
config['hg19_snp_file'] = '/home/treece/Download/snps_hg19.vcf.gz'

t0 = time.time()

# diagnostics
def trace (level, msg, stream=sys.stderr):
    if level <= config['verbosity']:
        if level == 0:
            print(msg)
        else:
            print(msg, file=stream)
            stream.flush()


# command-line arguments
parser = argparse.ArgumentParser(
    prog='snpinfo.py',
    description='Show information about SNPs by name or position',
    epilog='''e.g. snpinfo -s U106; snpinfo -s 8928037 -b hg38''')

parser.add_argument('-s', '--snp', nargs=1, help='specify SNP by pos or name')
parser.add_argument('-b', '--build', nargs=1, help='limit to build, e.g. hg38')
parser.add_argument('-C', '--create', action='store_true',
                        help='create the database of snps from a .vcf file')
args = parser.parse_args()


# create a sqlite database, cursor, and tables
dbconn = sqlite3.connect(config['db_file'])
dbcurs = dbconn.cursor()

# database schema - table and index creation when running with -C
SCHEMA = '''
/* list of all variants known for this computation */
drop table if exists variants;
create table variants(
    ID INTEGER PRIMARY KEY,
    buildID INTEGER references build(ID),
    pos INTEGER,
    anc INTEGER references alleles(ID),
    der INTEGER references alleles(ID),
    UNIQUE(buildID, pos, anc, der)
    );
/* allele values, strings of DNA letters */
drop table if exists alleles;
create table alleles(
    ID INTEGER PRIMARY KEY,
    allele TEXT,                  -- the allele value, e.g. "A" or "TTGT"
    UNIQUE(allele)
    );
/* names and aliases associated with variants */
drop table if exists snpnames;
create table snpnames(
    vID INTEGER REFERENCES variants(ID),
    snpname TEXT,
    unique(snpname,vID)
    );
create index snpidx1 on snpnames(snpname);
create index snpidx2 on snpnames(vID);
/* build (reference genome assembly) associated with data sets */
drop table if exists build;
create table build(
    ID INTEGER PRIMARY KEY,
    buildNm TEXT,
    unique(buildNm)
    );
'''


# create the database tables and indexes to hold SNP definitions
def create_tables():
    dbcurs.executescript(SCHEMA)
    return


# add to a SNP database from an input vcf data file
def build_snp_db(build, vcfpath):
    vcftab = pysam.VariantFile(vcfpath)
    allvals = set()
    for rec in vcftab.fetch():
        ref = rec.ref
        alt = rec.alts[0]
        allvals.add(ref)
        allvals.add(alt)
    trace(10, 'len(allvals): {}'.format(len(allvals)))
    dbconn.commit()
    dbcurs.executemany('insert or ignore into alleles(allele) values(?)',
                           allvals)
    variants = []
    for rec in vcftab.fetch():
        pos = rec.pos
        ref = rec.ref
        alt = rec.alts[0]
        alleles = rec.alleles
        if ref != alleles[0] or alt != alleles[1] or len(alleles) != 2:
            continue # reject this one - don't know what to do
        dbcurs.execute('select id from alleles where allele=?', (ref,))
        id1 = dbcurs.fetchone()[0]
        dbcurs.execute('select id from alleles where allele=?', (alt,))
        id2 = dbcurs.fetchone()[0]
        names = rec.id.split(',')
        for nm in names:
            variants.append((build, pos, id1, id2, nm))

    trace(10, 'len(variants): {}'.format(len(variants)))
    dbcurs.executemany('''insert or ignore into variants(buildid,pos,anc,der)
                          values(?,?,?,?)''',
                    list([l[0:4] for l in variants]))
    dbconn.commit()

    snpnames = [(l[4], l[0], l[1], l[2], l[3]) for l in variants if l[4]]
    dbcurs.executemany('''insert or ignore into snpnames(snpname,vid)
                          select ?, v.id from variants v
                          where v.buildid=? and v.pos=? and
                          v.anc=? and v.der=?''',
                     snpnames)
    dbconn.commit()

    return


# print info about a snp by name or addr
def querysnp(snp, bldid=None):
    trace(6, 'looking for details about {}...'.format(snp))
    c1 = dbconn.cursor()
    ids = set()
    try:
        # find variants if specified as pos.ref.alt
        pos,ref,alt = snp.split('.')
        c1.execute('''select v.id from variants v
                 inner join alleles a on a.id=v.anc
                 inner join alleles b on b.id=v.der
                 where v.pos=? and a.allele=? and b.allele=?''',
                 (pos,ref,alt))
    except:
        # find variants if specified as position or database id
        c1.execute('''select v.id from variants v where pos=?
                           union
                      select v.id from variants v where id=?''', (snp,snp))
    for row in c1:
        ids.add(row[0])
    # find variants if specified by SNP name
    c1.execute('select vid from snpnames where snpname=?', (snp.upper(),))
    for row in c1:
        ids.add(row[0])

    # if limiting search to a specific build, filter down the ids
    if bldid:
        tups = [(i,bldid) for i in ids]
        trace(10, 'variants to find: {}'.format(tups))
        id2 = set()
        for tup in tups:
            c1.execute('select id from variants where id=? and buildID=?', tup)
            try:
                id2.add(c1.fetchone()[0])
            except:
                pass
        ids = id2

    trace(10, 'found variant ids: {}'.format(ids))

    for id in ids:
        nams = set()
        # find any names this variant may have
        c1.execute('select distinct snpname from snpnames where vid=?', (id,))
        for row in c1:
            nams.add(row[0])

        c1.execute('''select distinct bld.buildnm, v.pos, a.allele as anc,
                           b.allele as der, v.id
                           from variants v
                           inner join alleles a on a.id=v.anc
                           inner join alleles b on b.id=v.der
                           inner join build bld on bld.id=v.buildid
                           where v.id=?''', (id,))
        for row in c1:
            if row[4] in ids:
                print('{} {:>8}.{}.{} - {} (id={})'.format(row[0], row[1],
                                                        row[2], row[3],
                                                        '/'.join(nams),
                                                        row[4]))
    if not ids:
        print('No data on {}'.format(snp))


if args.create:
    create_tables()
    dbcurs.executemany('insert into build(id,buildNm) values(?,?)',
                           ((1,'hg38'), (2,'hg19')))
    build_snp_db(1, config['hg38_snp_file'])
    build_snp_db(2, config['hg19_snp_file'])

if args.snp:
    if args.build:
        trace(10,'build argument: {}'.format(args.build))
        dbcurs.execute('select id from build where buildnm=?', args.build)
        bid = dbcurs.fetchone()[0]
    else:
        bid = None
    querysnp(args.snp[0], bid)

dbconn.commit()
dbcurs.close()
trace(10, 'done at {:.2f} seconds'.format(time.time() - t0))

