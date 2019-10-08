from __future__ import print_function, unicode_literals

import sys
import logging

from MySQLdb import OperationalError
from metapub.utils import remove_chars

from medgen.api import ClinVarDB

log = logging.getLogger('text2gene')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

PROMPT_STRING = ' *>'
PROMPT_YN = ' n>'

print()
print('Variants-in-Gene sample table creator')
print()
print('Enter a short nickname for this sampleset (e.g. "epilepsy"). (Special chars will be stripped.)')
reply = input(PROMPT_STRING)

nickname = remove_chars(reply)
nickname = reply.replace(' ', '_')

print()
print('Your new sample table shall be known as: samples_%s' % nickname)
print('Does this please you? (Enter "y" to confirm.)')
reply = input(PROMPT_YN)

if 'y' in reply.lower():
    print()
    print('Groovy.')

else:
    print()
    print('Was that a No? Quitting... (Consent is not enough, desire is!)')
    print()
    sys.exit()

print()
print('OK, now supply at least one gene name, or several on a line (space-separated), to draw variants from.')
reply = input(PROMPT_STRING)
if reply.strip() == '':
    print()
    print('Not in the mood? OK! Catch you later.')
    sys.exit()

clinsig = ''
print()
print('Great. Let\'s talk Clinical Significance. Do you prefer variants (1) Pathogenic (2) Benign (3) VUS or (blank) all?')
reply = input(PROMPT_STRING)
if reply.strip() == '':
    print()
    print('OK, all of em!')
elif reply.strip() == '1':
    print()
    print('Pathogenic it is.')
    clinsig = 'pathogenic'
elif reply.strip() == '2':
    print()
    print('Benign is fine.')
    clinsig = 'benign'
elif reply.strip() == '3':
    print()
    print('VUS, ooh, mysterious.')
    clinsig = 'vus'

db = ClinVarDB()

if clinsig:
    nickname = nickname + '_' + clinsig
# Actually make the table, finally.
create_table_sql = 'create table samples_{} like samples'.format(nickname)

try:
    db.execute(create_table_sql)
except OperationalError as err:
    print('Table already found; dropping to rebuild from scratch.')
    db.execute('drop table samples_{}'.format(nickname))
    db.execute(create_table_sql)
    
# Collect the list of genes
genes = reply.strip().split(' ')

#gene_str = ','.join(['"%s"' % gene for gene in genes])

get_variants_sql = 'insert into samples_'+nickname+' select * from samples'
if clinsig:
    get_variants_sql += '_'+clinsig
get_variants_sql += ' where GeneSymbol = "%s"'

print(get_variants_sql)
for gene in genes:
    db.execute(get_variants_sql % gene)

rows = db.fetchall('select * from samples_'+nickname)

print()
print('Done: new table samples_%s has %i entries.' % (nickname, len(rows)))
print()

