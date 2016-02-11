from __future__ import print_function

import json
import math
import re
import sys

from pubtatordb import SQLData

TABLENAME_TEMPLATE = 'm2p_%s'

# limit of rows to collect, for testing purposes. Set to None to turn off testing.
ROW_LIMIT = 10

component_patterns = {
    'DEL': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>DEL)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
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

FH_UNHANDLED = open('m2p_unhandled.dump', 'w')
def write_unhandled_row(row):
    FH_UNHANDLED.write(json.dumps(row) + '\n')
    FH_UNHANDLED.flush()


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


def parse_components(components):
    for name, re_patt in list(component_patterns.items()):
        match = re_patt.search(components)
        if match:
            return match.groupdict()

    if components.startswith('rs'):
        return {'RS': components, 'EditType': 'rs'}

    else:
        return None


def create_new_row(db, row):
    """
    :param db: SQLData object opened to MySQL PubTator database
    :param row: dictionary containing mutation2pubtator row
    :returns: bool (True if row creation worked, False otherwise)
    """
    new_row = row.copy()
    try:
        component_dict = parse_components(row['Components'])
        if component_dict:
            new_row.update(component_dict)
        else:
            write_unhandled_row(row)
            return False
    except Exception as error:
        print()
        print('> Error parsing row with components=%s: %r' % (row['Components'], error))
        print()
        return False

    db.insert('m2p_'+new_row['EditType'], new_row)
    return True


def get_new_row(row):
    """
    :param row: dictionary containing m2p row
    :returns: new_row (dict) with values for new table or None if components unparseable.
    """
    new_row = row.copy()
    try:
        component_dict = parse_components(row['Components'])
        if component_dict:
            new_row.update(component_dict)
        else:
            write_unhandled_row(row)
            return None
        new_row.update(component_dict)
        return new_row
    except Exception as error:
        print()
        print('> Error parsing row with components=%s: %r' % (row['Components'], error))
        print()
        return None


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
        else:
            create_component_table(db, key)

        print('@@@ Created %s table in PubTator database.' % tname)
        print('')

    # CREATE NEW TABLE 

    return db


def main_one_row_at_a_time():
    db = setup_db()

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


def main():
    db = setup_db()

    print('@@@ Finished creating tables. Populating!')
    print('')

    # create a dictionary with one empty list per component pattern in a new_rows hash
    new_rows = dict(zip(component_patterns.keys(), [[] for key in component_patterns.keys()]))

    table = json.loads(open('m2p.json', 'r').read())
    progress_tick = int(round(math.log(len(table))))

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
    for edit_type, rows in list(new_rows.items()):
        tname = TABLENAME_TEMPLATE % edit_type
        print('@@@ Adding %i rows to %s table' % (len(rows), tname))

        if ROW_LIMIT:
            rows = rows[:ROW_LIMIT]
        db.batch_insert(tname, rows)
        total_added += len(rows)

    print('Total inserted in new tables:', total_added)
    print('Unparseable:', broken)
    print('----------------')
    print('Processed:', total + broken)

    assert total_added == total


if __name__ == '__main__':
    main()

