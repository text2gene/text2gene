from text2gene.cached import ClinvarCachedQuery, PubtatorCachedQuery, NCBIVariantPubmedsCachedQuery

ClinvarCachedQuery().create_table()
PubtatorCachedQuery().create_table()
NCBIVariantPubmedsCachedQuery().create_table()

