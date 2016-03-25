from text2gene.cached import ClinvarCachedQuery, PubtatorCachedQuery 
from text2gene.ncbi import NCBIVariantReportCachedQuery, NCBIVariantPubmedsCachedQuery, NCBIEnrichedLVGCachedQuery
from text2gene.lvg_cached import HgvsLVGCached
from text2gene.training import Experiment

HgvsLVGCached().create_table()
ClinvarCachedQuery().create_table()
PubtatorCachedQuery().create_table()
NCBIVariantPubmedsCachedQuery().create_table()
NCBIVariantReportCachedQuery().create_table()
NCBIEnrichedLVGCachedQuery().create_table()

HgvsLVGCached().create_granular_table()
ClinvarCachedQuery().create_granular_table()
PubtatorCachedQuery().create_granular_table()
NCBIVariantPubmedsCachedQuery().create_granular_table()
NCBIVariantReportCachedQuery().create_granular_table()
NCBIEnrichedLVGCachedQuery().create_granular_table()

Experiment('generic', hgvs_examples=['fake']).create_table()

