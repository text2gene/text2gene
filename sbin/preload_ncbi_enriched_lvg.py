from __future__ import absolute_import, print_function

import time

from medgen.api import ClinVarDB
from text2gene.api import LVGEnriched, NCBIHgvs2Pmid
from hgvs_lexicon.exceptions import CriticalHgvsError


hgvs_examples = ClinVarDB().fetchall('select * from clinvar_hgvs order by rand() limit 200000')  # limit 10')

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

