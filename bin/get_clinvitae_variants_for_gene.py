from __future__ import print_function, unicode_literals

import sys

import requests

from metavariant import Variant
from metavariant.exceptions import *

from medgen.api import ClinvarAccession, ClinvarVariationID
from text2gene import LVGEnriched

# Patrick Short wrote a wrapper around the ClinVitae REST api:
# https://pythonhosted.org/bioservices/_modules/bioservices/clinvitae.html
#
# the only real endpoint needed, though:
# http://clinvitae.invitae.com/api/v1/variants?q=%s

def _get_variants_for_term(term):
    API_ENDPOINT = 'http://clinvitae.invitae.com/api/v1/variants?q=%s' 
    response = requests.get(API_ENDPOINT % term) 
    if response.ok:
        return response.json()
    else:
        raise Exception('Clinvitae Remote Error: status code %r returned for %s' % (response.status_code, API_ENDPOINT % term))


dups = {}
for item in data:
    hgvs_text = item['defaultNucleotideChange']
    if hgvs_text.replace('-', '').strip() == '':
        print('empty')
    else:
        try:
            dups[hgvs_text].append(item)
        except:
            dups[hgvs_text] = [item]
        vset.add(item['defaultNucleotideChange'])


for dup in dups:
    entries = dups[dup]
    if len(entries) > 1:
        print(dup)
        for entry in entries:
            print(entry['source'], entry.get('submitter'), entry['reportedClassification'])
            if entry['source'] == 'Invitae':
                print(entry.get('submitterComment'))
                if entry.get('submitterComment'):
                    comments += 1




if __name__ == '__main__':
    try:
        symbol = sys.argv[1]
    except IndexError:
        print()
        print('Supply gene symbol (e.g. "UGT1A1") as argument to this script.')
        print()
        sys.exit()


data = _get_variants_for_term(symbol)

#print(data)

from IPython import embed; embed()

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
