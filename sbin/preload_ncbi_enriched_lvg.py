from __future__ import absolute_import, print_function

import time

from medgen.api import ClinVarDB
from text2gene.api import LVGEnriched, NCBIHgvs2Pmid
from metavariant.exceptions import CriticalHgvsError
from metavariant.config import UTA_HOST, UTA_PORT


hgvs_examples = ClinVarDB().fetchall('select * from samples order by rand() limit 200000')  # limit 10')

print()
print('Using UTA host at %s:%r' % (UTA_HOST, UTA_PORT))
print()
print('%i HGVS examples found' % len(hgvs_examples))
print()

def dmesg(hgvs_text, msg):
    print('[%s] <%i> %s' % (hgvs_text, time.time(), msg))

for entry in hgvs_examples:
    hgvs_text = entry['hgvs_text']
    dmesg(hgvs_text, 'collecting')
    try:
        lex = LVGEnriched(hgvs_text)
    except CriticalHgvsError as error:
        print(error)
        continue

    pmids = NCBIHgvs2Pmid(hgvs_text)
    dmesg(hgvs_text, 'PMIDs: %r' % pmids)
    dmesg(hgvs_text, '%r' % lex.variants)
    dmesg(hgvs_text, 'done')

