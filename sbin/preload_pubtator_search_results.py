from __future__ import absolute_import, print_function

import time

from medgen.api import ClinVarDB
from text2gene import PubtatorHgvs2Pmid, ClinvarHgvs2Pmid
from text2gene.api import LVG

hgvs_examples = ClinVarDB().fetchall('select * from samples_vus')

print()
print('PUBTATOR')
print()
print('%i HGVS examples found in ClinVarDB.samples' % len(hgvs_examples))
print()

def dmesg(hgvs_text, msg):
    print('[%s] <%i> %s' % (hgvs_text, time.time(), msg))

for entry in hgvs_examples:
    hgvs_text = entry['HGVS']
    dmesg(hgvs_text, 'processing in PubTator (test case) and ClinVar (identity case)')
    lex = LVG(hgvs_text)
    #try:
    pmids = PubtatorHgvs2Pmid(lex)
    dmesg(hgvs_text, 'Pubtator PMIDs: %r' % pmids)
    #except Exception as error:
    #    dmesg(hgvs_text, '%r' % error)

    #try:
    pmids = ClinvarHgvs2Pmid(lex)
    dmesg(hgvs_text, 'ClinVar PMIDs: %r' % pmids)
    #except Exception as error:
    #    dmesg(hgvs_text, '%r' % error)
        
    dmesg(hgvs_text, 'done')

