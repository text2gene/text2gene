from __future__ import print_function, unicode_literals

import json
import math
import re
import sys

from metavariant import VariantComponents

from pubtatordb.sqldata import SQLData
from pubtatordb.config import get_data_log

log = get_data_log('logs/sqldata.log')

TABLENAME_TEMPLATE = 'm2p_%s'
M2P_JSON_DATA = 'data/m2p.json'

# limit of rows to collect, for testing purposes. Set to None to turn off testing.
ROW_LIMIT = 100

# === Mutation Component Types, with examples and tmVar format statements === #
# 
# http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/tutorial/tmVar.html
#
# Glossary:
#           <wild type>: Ref
#           <mutation position>: Pos
#           <mutant>: Alt
#
# FRAMESHIFT (FS)
#   tmVar: <Sequence type>|FS|<wild type>|<mutation position>|<mutant>|<frame shift position>
#   examples: p|FS|I|359|L|III      p|FS|89|R <-- very minority case (2 items), explicitly not handled right now.
#
# Insertion+Deletion:
#   tmVar: <Sequence type>|INDEL|<mutation position>|<mutant>
#   example: c|INDEL|2153_2155|TCCTGGTTTA
#
# Duplication:
#   tmVar: <Sequence type>|DUP|<mutation position>|<mutant>|<duplication times>
#   e.g.,   "c.1285-1301dup"    --> "c|DUP|1285_1301||"
#   e.g.,   "c.1978(TATC)(1-2)" --> "c|DUP|1978|TATC|1-2"
#

component_patterns = {
    'DEL': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>DEL)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'INS': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>INS)\|(?P<Pos>.*?)\|(?P<Alt>.*?)$'),
    'SUB': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>SUB)\|(?P<Ref>.*?)\|(?P<Pos>.*?)\|(?P<Alt>.*?)$'),
    'FS':  re.compile('^(?P<SeqType>.*?)\|(?P<EditType>FS)\|(?P<Ref>.*?)\|(?P<Pos>.*?)\|(?P<Alt>.*?)\|(?P<FS_Pos>.*?)$'),
    'INDEL': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>INDEL)\|(?P<Pos>.*?)\|(?P<Alt>.*?)$'),
    #'DUP': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>DUP)\|(?P<Pos>.*?)\|(?P<Alt>.*?)\|(?P<DupX>.*?)$'),
    'rs':  re.compile('^(?P<SeqType>rs)<?P<RS>.*?'),
}

# Data looks like this:
"""
{'Components': 'p|SUB|T|415|N', 'Mentions': 'Thr415Asn', 'PMID': 10072423},
{'Components': '|DEL|202_203|AG','Mentions': '202-203delAG','PMID': 10072423},
{'Components': '|DEL|255|A', 'Mentions': '255delA', 'PMID': 10072423},
{'Components': '|INS|321_322|GT','Mentions': '321-322insGT','PMID': 10072423},
{"PMID": 10371079, "Mentions": "A3243G", "Components": "|SUB|A|3243|G"}, 
{"PMID": 10760203, "Mentions": "RS2000", "Components": "rs2000"},
"""

FH_UNHANDLED = open('data/m2p_unhandled.dump', 'w')
def write_unhandled_row(row):
    FH_UNHANDLED.write(json.dumps(row) + '\n')
    FH_UNHANDLED.flush()

FH_MISSING_POSITION = open('data/m2p_missing_position.dump', 'w')
def write_missing_position(row):
    FH_MISSING_POSITION.write(json.dumps(row) + '\n')
    FH_MISSING_POSITION.flush()



def create_all_edittype_table(db):
    """Creates an m2p_general table to store mixed bag of all edit types.

    (Useful mostly for aminochange searches.)

    :param db: SQLData object already connected to MySQL PubTator database.
    """
    db.execute('''CREATE TABLE m2p_general (
      PMID int(10) unsigned DEFAULT NULL,
      Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
      Mentions text COLLATE utf8_unicode_ci NOT NULL,
      SeqType varchar(255) default NULL,
      EditType varchar(255) default NULL,
      Ref varchar(255) default NULL,
      Pos varchar(255) default NULL,
      Alt varchar(255) default NULL,
      DupX varchar(255) default NULL,
      FS_Pos varchar(255) default NULL,
      RS varchar(255) default NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci''')


def create_component_table(db, edit_type):
    """Creates an m2p_<EditType> table depending on the supplied `edit_type`

    e.g. edit_type='SUB' -->  m2p_SUB table created in PubTator database.

    :param db: SQLData object already connected to MySQL PubTator database.
    :param edit_type: str
    """
    db.execute('''CREATE TABLE m2p_%s (
      PMID int(10) unsigned DEFAULT NULL,
      Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
      Mentions text COLLATE utf8_unicode_ci NOT NULL,
      SeqType varchar(255) default NULL,
      EditType varchar(255) default NULL,
      Ref varchar(255) default NULL,
      Pos varchar(255) default NULL,
      Alt varchar(255) default NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci''' % edit_type)


def create_dup_table(db):
    """Creates an m2p_DUP table with special DupX column (varchar).

    :param db: SQLData object already connected to MySQL PubTator database.
    """
    db.execute('''CREATE TABLE m2p_DUP (
      PMID int(10) unsigned DEFAULT NULL,
      Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
      Mentions text COLLATE utf8_unicode_ci NOT NULL,
      SeqType varchar(255) default NULL,
      EditType varchar(255) default NULL,
      Ref varchar(255) default NULL,
      Pos varchar(255) default NULL,
      Alt varchar(255) default NULL,
      DupX varchar(255) default NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci''')


def create_fs_table(db):
    """Creates an m2p_FS table with special FS_Pos column (varchar).

    :param db: SQLData object already connected to MySQL PubTator database.
    """
    db.execute('''CREATE TABLE m2p_FS (
      PMID int(10) unsigned DEFAULT NULL,
      Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
      Mentions text COLLATE utf8_unicode_ci NOT NULL,
      SeqType varchar(255) default NULL,
      EditType varchar(255) default NULL,
      Ref varchar(255) default NULL,
      Pos varchar(255) default NULL,
      Alt varchar(255) default NULL,
      FS_Pos varchar(255) default NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci''')


def create_rs_table(db):
    """Creates an m2p_rs table for storing SNP rs references.

    :param db: SQLData object already connected to MySQL PubTator database.
    """
    db.execute('''CREATE TABLE m2p_rs (
      PMID int(10) unsigned DEFAULT NULL,
      Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
      Mentions text COLLATE utf8_unicode_ci NOT NULL,
      EditType varchar(255) default NULL,
      RS varchar(255) default NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci''')


def create_gene2mutation2pubmed_table(db):
    """Creates table mapping GeneID to PMID to Components."""
    db.drop_table('gene2mutation2pubmed')
    db.execute('''create table gene2mutation2pubmed
        select distinct  G.GeneID, G.PMID, M.Components
                   from  gene2pubtator G, mutation2pubtator M
                   where G.PMID=M.PMID''')
    db.execute('call create_index("gene2mutation2pubmed", "Components")')
    db.execute('call create_index("gene2mutation2pubmed", "GeneID")')
    db.execute('call create_index("gene2mutation2pubmed", "GeneID,PMID")')
    db.execute('call create_index("gene2mutation2pubmed", "GeneID,Components")')


def parse_components(components):
    for name, re_patt in list(component_patterns.items()):
        match = re_patt.search(components)
        if match:
            comp_dict = match.groupdict()
            # verify that this is an entry that actually helps us; remove any 
            # entry that doesn't have a valid position (Pos).
            if comp_dict['Pos'].strip() == '':
                write_missing_position(comp_dict)
                return None

            components = VariantComponents(**comp_dict)
            return components.to_mysql_dict()

    if components.startswith('rs'):
        return {'RS': components, 'EditType': 'rs'}

    else:
        return None


def get_new_row(row):
    """
    :param row: dictionary containing m2p row
    :returns: new_row (dict) with values for new table or None if components unuseable/unparseable.
    """
    if row['Components'] is None:
        return None

    new_row = row.copy()
    component_dict = parse_components(row['Components'])
    if component_dict:
        new_row.update(component_dict)
    else:
        write_unhandled_row(row)
        return None
    new_row.update(component_dict)
    return new_row


def setup_db():
    """ Set up connection to MySQL. Drop existing tables in PubTator DB relating to
    mutation2pubtator components. (Re)make these tables.  Return SQLData object.

    :returns db: SQLData object connected to MySQL
    """
    db = SQLData()

    # Hello, are you there MySQL? It's me, python.
    db.ping()

    # DROP EXISTING TABLES! 
    # CREATE NEW TABLES!  One each for SUB, DEL, and INS.
    for key in component_patterns:
        tname = TABLENAME_TEMPLATE % key
        db.drop_table(tname)
        if key == 'rs':
            create_rs_table(db)
        elif key == 'FS':
            create_fs_table(db)
        elif key == 'DUP':
            create_dup_table(db)
        else:
            create_component_table(db, key)

        print('@@@ Created %s table in PubTator database.' % tname)
        print('')

    # m2p_general
    db.drop_table('m2p_general')
    create_all_edittype_table(db)
    print('@@@ Created m2p_general table in PubTator database.')
    print('')

    print('@@@ Setting up gene2mutation2pubmed table (with indexes)...')
    create_gene2mutation2pubmed_table(db)
    return db

def create_indices(db):
    # CREATE INDEXES on each component part column.
    print('@@@ Creating indexes on all tables...')
    for key in component_patterns:
        if key != 'rs':
            db.execute("call create_index('m2p_%s', 'SeqType')" % key)
            db.execute("call create_index('m2p_%s', 'EditType')" % key)
            db.execute("call create_index('m2p_%s', 'Ref')" % key)
            db.execute("call create_index('m2p_%s', 'Pos')" % key)
            db.execute("call create_index('m2p_%s', 'Alt')" % key)

    # m2p_general
    db.execute("call create_index('m2p_general', 'Ref')")
    db.execute("call create_index('m2p_general', 'Pos')")
    db.execute("call create_index('m2p_general', 'Alt')")
    db.execute("call create_index('m2p_general', 'SeqType')")
    db.execute("call create_index('m2p_general', 'EditType')")

def main_one_at_a_time():
    db = setup_db()

    print('@@@ Finished creating tables and indexing.')
    print('@@@ Parsing components...')

    # create a dictionary with one empty list per component pattern in a new_rows hash
    new_rows = dict(zip(component_patterns.keys(), [[] for key in component_patterns.keys()]))

    table = json.loads(open(M2P_JSON_DATA, 'r').read())
    progress_tick = int(round(math.log(len(table)))) * 100

    broken = 0
    total = 0
    for row in table:
        new_row = get_new_row(row)
        if new_row:
            total += 1
            if total % progress_tick == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            db.insert('m2p_' + new_row['EditType'].upper(), new_row)

            # m2p_general
            db.insert('m2p_general', new_row)

        else:
            broken += 1

    create_indices(db)

    print('')
    print('@@@ RESULTS:')
    print('Total rows processed from mutation2pubtator:', total + broken)
    print('Total inserted in new tables:', total)
    print('Unparseable or Unuseable:', broken)
    print('')
    print('@@@ DONE')


def main():
    db = setup_db()

    print('@@@ Finished creating tables and indexing.') 
    print('@@@ Parsing components...')

    # create a dictionary with one empty list per component pattern in a new_rows hash
    new_rows = dict(zip(component_patterns.keys(), [[] for key in component_patterns.keys()]))

    table = json.loads(open(M2P_JSON_DATA, 'r').read())
    progress_tick = int(round(math.log(len(table)))) * 100

    broken = 0
    total = 0
    for row in table:
        new_row = get_new_row(row)
        if new_row:
            total += 1
            if total % progress_tick == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
            new_rows[new_row['EditType']].append(new_row)

        else:
            broken += 1

    total_added = 0

    print('\n@@@ Parsing complete -- populating tables!')

    for edit_type, rows in list(new_rows.items()):
        tname = TABLENAME_TEMPLATE % edit_type
        print('\n@@@ Adding %i rows to %s table' % (len(rows), tname))

        row_index = 0
        while row_index < len(rows):
            db.batch_insert(tname, rows[row_index:row_index + ROW_LIMIT])

            # m2p_general
            db.batch_insert('m2p_general', rows[row_index:row_index + ROW_LIMIT])
            row_index = row_index + ROW_LIMIT

        total_added += len(rows)

    create_indices(db)
    print('')
    print('@@@ RESULTS:')
    print('Total rows processed from mutation2pubtator:', total + broken)
    print('Total inserted in new tables:', total_added)
    print('Unparseable or Unuseable:', broken)
    print('')
    print('@@@ DONE')


if __name__ == '__main__':
    #main_one_at_a_time()
    main()

