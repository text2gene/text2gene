from __future__ import absolute_import, print_function, unicode_literals

import logging
#import requests

from hgvs_lexicon import HgvsComponents, RejectedSeqVar

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
    gquery_tmpl = '"{gene_name}" {posedit_clause}'

    if not lex.gene_name:
        log.debug('No gene_name for SequenceVariant %s', lex.seqvar)
        return None

    posedits = set()

    for seqvar in lex.seqvars:
        try:
            comp = HgvsComponents(seqvar)
        except RejectedSeqVar as error:
            print(error)
            continue

        # 1) Offical
        posedits.add('"%s"' % comp.posedit)

        # 2) Slang
        try:
            for item in comp.posedit_slang:
                posedits.add('"%s"' % item)
        except NotImplementedError as error:
            log.debug(error)

    posedit_clause = '(%s)' % '|'.join(posedits)
    return gquery_tmpl.format(gene_name=lex.gene_name, posedit_clause=posedit_clause)


if __name__ == '__main__':
    test_sub = "NM_014874.3:c.891C>T"
    sub_expected = '"MFN2" ("891C>T"|"891C->T"|"891C-->T"|"891C/T"|"C891T"|"1344C>U"|"1344C->U"|"1344C-->U"|"1344C/U"|"C1344U")'

    test_del = 'NM_007294.3:c.4964_4982delCTGGCCTGACCCCAGAAGA'
    del_expected = '"BRCA1" ("4964_4982delCTGGCCTGACCCCAGAAGA"|"4964_4982del"|"5196_5214delCUGGCCUGACCCCAGAAGA"|"5196_5214del"|"Ser1655TyrfsTer16"|"4823_4841delCTGGCCTGACCCCAGAAGA"|"4823_4841del"|"5104_5122delCUGGCCUGACCCCAGAAGA"|"5104_5122del"|"Ser1608TyrfsTer16"|"1652_1670delCTGGCCTGACCCCAGAAGA"|"1652_1670del"|"1846_1864delCUGGCCUGACCCCAGAAGA"|"1846_1864del"|"Ser551TyrfsTer16"|"1671_1689delCUGGCCUGACCCCAGAAGA"|"1671_1689del"|"5027_5045delCTGGCCTGACCCCAGAAGA"|"5027_5045del"|"5259_5277delCUGGCCUGACCCCAGAAGA"|"5259_5277del"|"Ser1676TyrfsTer16")'

    test_dup = 'NM_025114.3:c.6869dupA'
    dup_expected = '"CEP290" ("6869dupA"|"6869dup"|"7213dupA"|"7213dup"|"Asn2290LysfsTer6")'
