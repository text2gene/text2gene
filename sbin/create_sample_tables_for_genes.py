from __future__ import print_function, unicode_literals

import sys
import logging

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
reply = raw_input(PROMPT_STRING)

nickname = remove_chars(reply)
nickname = reply.replace(' ', '_')

print()
print('Your new sample table shall be known as: samples_%s' % nickname)
print('Does this please you? (Enter "y" to confirm.)')
reply = raw_input(PROMPT_YN)

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
reply = raw_input(PROMPT_STRING)
if reply.strip() == '':
    print()
    print('Not in the mood? OK! Catch you later.')
    sys.exit()


db = ClinVarDB()

# Actually make the table, finally.
create_table_sql = 'create table samples_{} like samples'.format(nickname)
res = db.execute(create_table_sql)
from IPython import embed; embed()

# Collect the list of genes
genes = reply.strip().split(' ')

gene_str = ','.join(['"%s"' % gene for gene in genes])

get_variants_sql = 'insert into samples_'+nickname+' select * from samples where Symbol in (%s)' % gene_str

for gene in genes:
    db.execute(get_variants_sql)

rows = db.fetchall('select * from samples_'+nickname)

print()
print('Done: new table samples_%s has %i entries.' % (nickname, len(rows)))
print()

