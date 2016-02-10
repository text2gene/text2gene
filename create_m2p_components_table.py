from __future__ import print_function

import json
import math
import re

from pubtatordb import SQLData

TABLENAME_TEMPLATE = 'm2p_%s'

component_patterns = { 'DEL': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>DEL)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'INS': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>INS)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'SUB': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>SUB)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
    'rs': re.compile('^(?P<SeqType>.*?)\|(?P<EditType>SUB)\|(?P<Pos>.*?)\|(?P<Ref>.*?)$'),
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

db = SQLData()

def create_component_table(edit_type):
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


def parse_components(components):
    for name, re_patt in list(component_patterns.items()):
        match = re_patt.search(components)
        if match:
            return match.groupdict()

def create_new_row(row):
    new_row = row.copy()
    try:
        component_dict = parse_components(row['Components'])
        new_row.update(component_dict)
    except Exception as error:
        return False

    db.insert('m2p_'+new_row['EditType'], new_row)
    return True


# Hello, are you there MySQL? It's me, python.
db.ping()

# DROP EXISTING TABLES! 
# CREATE NEW TABLES!  One each for SUB, DEL, and INS.
for key in component_patterns:
    db.drop_table(TABLENAME_TEMPLATE % key)
    create_component_table(key)
    print('@@@ Created m2p_components table in PubTator database.')
    print('')

print('@@@ Finished creating tables. Populating!')
print('')

new_rows = []

table = json.loads(open('m2p.json', 'r').read())
progress_tick = int(round(math.log(len(table))))

broken = 0
total = 0
for row in table:
    if create_new_row(row):
        total += 1
        if total % progress_tick == 0:
            print('.', end='', flush=True)
    else:
        broken += 1

print('Total inserted in new tables:', total)
print('Unparseable:', broken)
print('----------------')
print('Processed:', total + broken)

