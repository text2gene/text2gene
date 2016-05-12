from __future__ import absolute_import, print_function, unicode_literals

import sys
import logging

from text2gene.googlequery import GoogleQuery
from text2gene.api import LVGEnriched
from text2gene.exceptions import Text2GeneError

log = logging.getLogger('text2gene.*')
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

logging.getLogger('hgvs_lexicon').addHandler(ch)

UPDATE_CACHE = True


def dmesg(hgvs_text, msg):
    print('[%s] %s' % (hgvs_text, msg))

def print_result(hgvs_text, cseres, idx):
    if cseres.pmid:
        dmesg(hgvs_text, '%i) Resolved: %s' % (idx, cseres.pmid))
    else:
        dmesg(hgvs_text, '%i) Unresolved:' % idx)
    dmesg(hgvs_text, '    url: %s' % cseres.url)
    dmesg(hgvs_text, '    doi: %s' % cseres.doi)

try:
    hgvs_file = sys.argv[1]
except IndexError:
    print('Supply filename of text file containing list of hgvs_text samples as argument to this script.')
    sys.exit()

with open(hgvs_file) as fileh:
    hgvs_samples = [item for item in fileh.read().split('\n') if item.strip() != '']

for hgvs_text in hgvs_samples:
    lex = LVGEnriched(hgvs_text)
    
    try:
        cse_results = GoogleQuery(lex, skip_cache=UPDATE_CACHE)
    except Text2GeneError as error:
        print('@@@ Error querying Google')
        dmesg(hgvs_text, '%r' % error)
        print()
        dmesg(hgvs_text, 'Google query: %s' % gcse.build_query())
        continue

    dmesg(hgvs_text, 'Google CSE Results: %i' % len(cse_results))
    resolved = []
    idx = 0
    for cseres in cse_results:
        if cseres.pmid:
            resolved.append(cseres)
        print_result(hgvs_text, cseres, idx)
        idx += 1

    dmesg(hgvs_text, 'TOTAL RESOLVED: %i / %i' % (len(resolved), len(cse_results)))
    print()


