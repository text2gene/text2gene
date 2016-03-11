from __future__ import absolute_import, print_function

import time

from medgen.api import ClinVarDB
from text2gene import NCBIEnrichedLVG


hgvs_examples = ClinVarDB().fetchall('select * from hgvs_examples limit 10')

print()
print('%i HGVS examples found' % len(hgvs_examples))
print()

def dmesg(hgvs_text, msg):
    print('[%s] <%i> %s' % (hgvs_text, time.time(), msg))

for entry in hgvs_examples:
    hgvs_text = entry['hgvs_text']
    dmesg(hgvs_text, 'collecting')
    lex = NCBIEnrichedLVG(hgvs_text)
    dmesg(hgvs_text, '%r' % lex.variants)
    dmesg(hgvs_text, 'done')

