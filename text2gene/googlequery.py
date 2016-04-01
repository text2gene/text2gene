from __future__ import absolute_import, print_function, unicode_literals

import logging
#import requests

from hgvs_lexicon import HgvsComponents

log = logging.getLogger('text2gene.googlequery')

# Google API Key authorized for Servers
API_KEY = 'AIzaSyBbzzCZbm5ccB6MC1e0y_tRFeNBdeoutPo'

# Google query API endpoint
CSE_URL = "https://www.googleapis.com/customsearch/v1"

# query example:
#  GET https://www.googleapis.com/customsearch/v1?key=INSERT_YOUR_API_KEY&cx=017576662512468239146:omuauf_lfve&q=lectures


def GoogleQuery(lex):
    """ Quick-and-dirty git 'er done google query expansion.

    :param lex: *LVG* instance (HgvsLVG | NCBIEnrichedLVG | LVGEnriched | LVG object)
    :returns: string containing expanded google query for variant
    """

    test_hgvs_text = "NM_014874.3:c.891C>T"
    expected = '"MFN2" ("891C>T"|"891C->T"|"891C-->T"|"891C/T"|"C891T"|"1344C>U"|"1344C->U"|"1344C-->U"|"1344C/U"|"C1344U"'

    for seqvar in lex.variants['c'].values() + lex.variants['g'].values():
        try:
            comp = HgvsComponents(seqvar)
        except RejectedSeqVar as error:
            print(error)
            continue

