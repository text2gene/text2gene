import sys

from text2gene.cached import ClinvarCachedQuery, PubtatorCachedQuery 
from text2gene.ncbi import NCBIVariantReportCachedQuery, NCBIVariantPubmedsCachedQuery, NCBIEnrichedLVGCachedQuery
from text2gene.lvg_cached import HgvsLVGCached
from text2gene.experiment import Experiment

try:
    reset = sys.argv[1].lower()
    if reset == 'reset':
        reset = True
    else:
        reset = False
except IndexError:
    reset = False

HgvsLVGCached().create_table(reset)
ClinvarCachedQuery().create_table(reset)
PubtatorCachedQuery().create_table(reset)
NCBIVariantPubmedsCachedQuery().create_table(reset)
NCBIVariantReportCachedQuery().create_table(reset)
NCBIEnrichedLVGCachedQuery().create_table(reset)

# HgvsLVGCached().create_granular_table(reset)
# ClinvarCachedQuery().create_granular_table(reset)
# PubtatorCachedQuery().create_granular_table(reset)
# NCBIVariantPubmedsCachedQuery().create_granular_table(reset)
# NCBIVariantReportCachedQuery().create_granular_table(reset)
# NCBIEnrichedLVGCachedQuery().create_granular_table(reset)

Experiment('generic', hgvs_examples=['fake']).create_table()

