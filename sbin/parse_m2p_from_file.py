from __future__ import print_function

import json

from pubtatordb import sqldata

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
new_rows = []

table = json.loads(open('m2p.json', 'r').read())

total_sub = 0
total_other = 0
for row in table:
    if row['Components']:
        components = row['Components'].split('|')
    else:
        components = ['','','','','',]

    if len(components) < 5:
        total_other += 1
        # print(row)
        continue

    new_row = row.copy()
    new_row['seq_type'] = components[0]
    new_row['edit_type'] = components[1]
    new_row['ref'] = components[2]
    new_row['pos'] = components[3]
    new_row['alt'] = components[4]

    new_rows.append(new_row)
    total_sub += 1

print('Total SUB rows:', total_sub)
print('Other types:', total_other)


