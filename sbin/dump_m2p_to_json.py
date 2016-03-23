import json

from pubtatordb import sqldata

M2P_JSON_DATA = 'data/m2p.json'

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

db = sqldata.SQLData()
table = db.fetchall('select * from mutation2pubtator')

new_rows = []
row_tmpl = {'Mentions': '', 'PMID': None, 'Components': '',
            'edit_type': False, 'seq_type': '', 'ref': '', 'pos': '', 'alt': '' }

open(M2P_JSON_DATA, 'w').write(json.dumps(table))

for row in table:
    print('')
    if row['Components']:
        components = row['Components'].split('|')
    else:
        components = ['','','','','',]

    if len(components) < 5:
        continue

    new_row = row.copy()
    new_row['seq_type'] = components[0]
    new_row['edit_type'] = components[1]
    new_row['ref'] = components[2]
    new_row['pos'] = components[3]
    new_row['alt'] = components[4]

    print(new_row)
    new_rows.append(new_row)

