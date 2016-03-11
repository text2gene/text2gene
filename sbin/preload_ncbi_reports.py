from __future__ import absolute_import, print_function

import time

from medgen.api import ClinVarDB
from text2gene.cached import NCBIReport

hgvs_examples = ClinVarDB().fetchall('select * from hgvs_examples')

print()
print('%i HGVS examples found' % len(hgvs_examples))
print()

def dmesg(hgvs_text, msg):
    print('[%s] <%i> %s' % (hgvs_text, time.time(), msg))

for entry in hgvs_examples:
    hgvs_text = entry['hgvs_text']
    dmesg(hgvs_text, 'collecting')
    try:
        report = NCBIReport(hgvs_text)
    except Exception as error:
        dmesg(hgvs_text, '%r' % error)

    dmesg(hgvs_text, 'done')

