import sys

from text2gene.cached import ClinvarCachedQuery, PubtatorCachedQuery 
from text2gene.lvg_cached import VariantLVGCached 
from text2gene.googlequery import GoogleCachedQuery

try:
    reset = sys.argv[1].lower()
    if reset == 'reset':
        reset = True
    else:
        reset = False
except IndexError:
    reset = False

VariantLVGCached().create_table(reset)
ClinvarCachedQuery().create_table(reset)
PubtatorCachedQuery().create_table(reset)
GoogleCachedQuery().create_table(reset)

# VariantLVGCached().create_granular_table(reset)
# ClinvarCachedQuery().create_granular_table(reset)
# PubtatorCachedQuery().create_granular_table(reset)

