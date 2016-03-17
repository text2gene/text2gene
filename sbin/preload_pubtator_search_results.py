from __future__ import absolute_import, print_function

import time

from medgen.api import ClinVarDB
from text2gene import PubtatorHgvs2Pmid, ClinvarHgvs2Pmid


hgvs_examples = ClinVarDB().fetchall('select * from hgvs_examples limit 2')

print()
print('PUBTATOR')
print()
print('%i HGVS examples found in ClinVarDB.hgvs_examples' % len(hgvs_examples))
print()

def dmesg(hgvs_text, msg):
    print('[%s] <%i> %s' % (hgvs_text, time.time(), msg))

for entry in hgvs_examples:
    hgvs_text = entry['hgvs_text']
    dmesg(hgvs_text, 'processing in PubTator (test case) and ClinVar (identity case)')
    try:
        pmids = PubtatorHgvs2Pmid(hgvs_text)
        dmesg(hgvs_text, 'Pubtator PMIDs: %r' % pmids)
    except Exception as error:
        dmesg(hgvs_text, '%r' % error)
        from IPython import embed; embed()

    try:
        pmids = ClinvarHgvs2Pmid(hgvs_text)
        dmesg(hgvs_text, 'ClinVar PMIDs: %r' % pmids)
    except Exception as error:
        dmesg(hgvs_text, '%r' % error)
        
    dmesg(hgvs_text, 'done')




