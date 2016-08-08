from __future__ import print_function, unicode_literals

import sys
import csv

from metavariant import Variant
from metavariant.exceptions import *

from medgen.api import ClinvarAccession, ClinvarVariationID
from text2gene import LVGEnriched

# Patrick Short wrote a wrapper around the ClinVitae REST api:
# https://pythonhosted.org/bioservices/_modules/bioservices/clinvitae.html
#
# the only real endpoint needed, though:
# http://clinvitae.invitae.com/api/v1/variants?q=%s


try:
    symbol = sys.argv[1]
except IndexError:
    print()
    print('Supply gene symbol (e.g. "UGT1A1") as argument to this script.')
    print()
    sys.exit()

with open('../data/clinvitae_FANCA_variant_results.tsv') as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter=bytes('\t'))
    for row in reader:
        hgvs_text = row['Nucleotide Change'].strip()
        try:
            lex = LVGEnriched(hgvs_text)
            #print(lex.variants)
            print(hgvs_text)
            print(row['Other Mappings'])
            print()
        except Exception as error:
            print(error)
            continue
            #print(hgvs_text)
            #print(row)


"""
lovd_variants = LOVDVariantsForGene(symbol, 'chromium.lovd.nl')

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
"""
