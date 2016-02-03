from pubtatordb import sqldata

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
            'protein': False, 'mutation_type': '', 'ref': '', 'pos': '', 'alt': '' }

for row in table:
    print('')
    components = row['components'].split('|')

    new_row = row.copy()
    new_row['protein'] = bool(components[0])
    new_row['mutation_type'] = components[1]
    new_row['ref'] = components[2]
    new_row['pos'] = components[3]
    new_row['alt'] = components[4]

    print(new_row)
    new_rows.append(new_row)

from IPython import embed; embed()

