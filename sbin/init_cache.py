from text2gene.cached import HgvsLVGCached, ClinvarCachedQuery, PubtatorCachedQuery, NCBIVariantPubmedsCachedQuery

HgvsLVGCached().create_table()
ClinvarCachedQuery().create_table()
PubtatorCachedQuery().create_table()
NCBIVariantPubmedsCachedQuery().create_table()

