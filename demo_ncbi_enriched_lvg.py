from __future__ import absolute_import, print_function, unicode_literals

from hgvs_lexicon import HgvsLVG, HgvsComponents, Variant
from text2gene.ncbi import NCBIEnrichedLVG


hgvs_text_no_uta_results = 'NM_194248.1:c.158C>T'

print()
print(hgvs_text_no_uta_results)
print()

lex1 = HgvsLVG(hgvs_text_no_uta_results)
lex2 = HgvsLVG(hgvs_text_no_uta_results, hgvs_g = ['NC_000002.11:g.26750769G>A'])

print('UTA ONLY:')
print(lex1.variants)
print()
print('####')
print()
print('UTA "enriched" by results from NCBI:')
print(lex2.variants)

print()
print('####')
print()

lex3 = NCBIEnrichedLVG(hgvs_text_no_uta_results)
print(lex3.variants)
