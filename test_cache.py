from text2gene.sqlcache import SQLCache

t2g_cache = SQLCache('t2g')
t2g_cache.create_table()

t2g_cache.store({'thing1': False}, 'SOME RESULT')
print(t2g_cache.get_row({'thing1': False}))
print(t2g_cache.retrieve({'thing1': False}))

print(t2g_cache.retrieve({'thing2': True}))

t2g_cache.store({'thing2': True}, value={'cat': 'hat'})
print(t2g_cache.retrieve({'thing2': True}))

print(t2g_cache.get_row({'thing2': True}))


####

from text2gene.pmid_lookups import ClinvarCache, PubtatorCache, NCBIVariantReporterCache

#NCBIVariantReporterCache.lookup(hgvs_text)

hgvs_text = 'NM_194248.1:c.158C>T'

if not PubtatorCache.retrieve({'hgvs_text': hgvs_text}):
    result = pubtator_hgvs_to_pmid(hgvs_text)
    PubtatorCache.store({'hgvs_text': hgvs_text}, result)

print(result)






