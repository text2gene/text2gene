from text2gene.cached import ClinvarCachedQuery, PubtatorCachedQuery, NCBIVariantReporterCachedQuery

ClinvarCachedQuery().create_table()
PubtatorCachedQuery().create_table()
NCBIVariantReporterCachedQuery().create_table()

