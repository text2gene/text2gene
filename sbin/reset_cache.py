from text2gene.cached import NCBIVariantReportCachedQuery, ClinvarCachedQuery, PubtatorCachedQuery, NCBIVariantPubmedsCachedQuery
from text2gene.lvg_cached import HgvsLVGCached

HgvsLVGCached().drop_table()
HgvsLVGCached().create_table()

ClinvarCachedQuery().drop_table()
ClinvarCachedQuery().create_table()

PubtatorCachedQuery().drop_table()
PubtatorCachedQuery().create_table()

NCBIVariantPubmedsCachedQuery().drop_table()
NCBIVariantPubmedsCachedQuery().create_table()

NCBIVariantReportCachedQuery().drop_table()
NCBIVariantReportCachedQuery().create_table()
