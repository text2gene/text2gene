from __future__ import print_function, unicode_literals

import sys

from metavariant.lovd import *
from metavariant.exceptions import *

from medgen.api import ClinvarAccession, ClinvarVariationID
from text2gene import LVGEnriched


try:
    symbol = sys.argv[1]
except IndexError:
    print()
    print('Supply gene symbol (e.g. "UGT1A1") as argument to this script.')
    print()
    sys.exit()


lovd_variants = LOVDVariantsForGene(symbol)

result_dict = {}

for hgvs_text in lovd_variants:
    try:
        lex = LVGEnriched(hgvs_text)
    except CriticalHgvsError as err:
        result_dict[hgvs_text] = 'error'
        print(hgvs_text, err)
        continue

    #print(lex.variants)
    result_dict[lex.hgvs_text] = {}
    in_clinvar = False
    for seqvar in lex.seqvars:
        varID = ClinvarVariationID('%s' % seqvar)
        result_dict[lex.hgvs_text]['%s' % seqvar] = varID
        if varID:
            in_clinvar = varID

    if in_clinvar:
        print(hgvs_text, in_clinvar)
    else:
        print(hgvs_text, 'Not in ClinVar!')

#from IPython import embed; embed()
#print(result_dict)

