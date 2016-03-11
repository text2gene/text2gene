from text2gene.cached import ClinvarCachedQuery, PubtatorCachedQuery, NCBIVariantPubmedsCachedQuery
from text2gene.lvg_cached import HgvsLVGCached

HgvsLVGCached().create_table()
ClinvarCachedQuery().create_table()
PubtatorCachedQuery().create_table()
NCBIVariantPubmedsCachedQuery().create_table()

