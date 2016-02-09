from __future__ import print_function

import json
import math

from pubtatordb import SQLData

# Data looks like this:
"""
 {'Components': 'p|SUB|T|415|N', 'Mentions': 'Thr415Asn', 'PMID': 10072423},
 {'Components': '|DEL|202_203|AG',
  'Mentions': '202-203delAG',
  'PMID': 10072423},
 {'Components': '|DEL|255|A', 'Mentions': '255delA', 'PMID': 10072423},
 {'Components': '|INS|321_322|GT',
  'Mentions': '321-322insGT',
  'PMID': 10072423},
"""

db = SQLData()

def create_new_row(row):
    """
    Using existing mutation2pubtator row, create a new row in the new
    m2p_components table by parsing apart the `Components` column.

    :param row: dictionary representing m2p row
    """
    if row['Components']:
        components = row['Components'].split('|')
    else:
        components = ['','','','','',]

    if len(components) < 5:
        return 0

    new_row = row.copy()
    new_row['SeqType'] = components[0]
    new_row['EditType'] = components[1]
    new_row['Ref'] = components[2]
    new_row['Pos'] = components[3]
    new_row['Alt'] = components[4]

    result = db.insert('m2p_components', row)
    print(result)
    return 1



# CREATE TABLE! (Automatically drops if it already exists.)
#os.popen('mysql -u medgen -pmedgen PubTator < create_m2p_component_table.sql')

db.drop_table(TABLENAME)

db.execute('''CREATE TABLE m2p_components (
  PMID int(10) unsigned DEFAULT NULL,
  Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
  Mentions text COLLATE utf8_unicode_ci NOT NULL,
  SeqType varchar(255) default NULL,
  EditType varchar(255) default NULL,
  Ref varchar(255) default NULL,
  Pos varchar(255) default NULL,
  Alt varchar(255) default NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;''')

print('Created m2p_components table in PubTator database.  Adding rows...')
print('')

new_rows = []

table = json.loads(open('m2p.json', 'r').read())
progress_tick = int(round(math.log(len(table))))

total_sub = 0
total = 0
for row in table:
    total += 1
    total_sub += create_new_row(row)
    if total % progress_tick == 0:
        print('TICK')

print('Total SUB rows:', total_sub)
print('Other types:', total - total_sub)
print('----------------')
print('Processed:', total)

