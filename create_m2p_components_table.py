from __future__ import print_function

import json
import math
import re
import sys

from pubtatordb import SQLData

TABLENAME_TEMPLATE = 'm2p_%s'

component_patterns = { 'DEL': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>DEL)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'INS': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>INS)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'SUB': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>SUB)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'rs': re.compile('^(?P<SeqType>rs)<?P<RS>.*?'),
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;''' % edit_type)


def create_rs_table(db):
    """Creates an m2p_rs table for storing SNP rs references.

    :param db: SQLData object already connected to MySQL PubTator database.
    """
    db.execute('''CREATE TABLE m2p_rs (
      PMID int(10) unsigned DEFAULT NULL,
      Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
      Mentions text COLLATE utf8_unicode_ci NOT NULL,
      EditType varchar(255) default NULL,
      RS varchar(255) default NULL,
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;''' % edit_type)


def parse_components(components):
    for name, re_patt in list(component_patterns.items()):
        match = re_patt.search(components)
        if match:
            return match.groupdict()

    if components.startswith('rs'):
        return { 'RS': components, 'EditType': 'rs' }


def create_new_row(db, row):
    """
    :param db: SQLData object opened to MySQL PubTator database
    :param row: dictionary containing mutation2pubtator row
    :returns: bool (True if row creation worked, False otherwise)
    """

    new_row = row.copy()
    try:
        component_dict = parse_components(row['Components'])
        new_row.update(component_dict)
    except Exception as error:
        return False

    db.insert('m2p_'+new_row['EditType'], new_row)
    return True


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
        create_component_table(db, key)
        print('@@@ Created %s table in PubTator database.' % tname)
        print('')

    return db


def main():

    print('@@@ Finished creating tables. Populating!')
    print('')

    new_rows = []

    table = json.loads(open('m2p.json', 'r').read())
    progress_tick = int(round(math.log(len(table))))

    broken = 0
    total = 0
    for row in table:
        if create_new_row(db, row):
            total += 1
            if total % progress_tick == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        else:
            broken += 1

    print('Total inserted in new tables:', total)
    print('Unparseable:', broken)
    print('----------------')
    print('Processed:', total + broken)


if __name__=='__main__':
    main()



