from text2gene.sqlcache import SQLCache

from text2gene.pmid_lookups import *

"""
t2g_cache = SQLCache('t2g')
t2g_cache.create_table()

t2g_cache.store({'thing1': False}, 'SOME RESULT')
print(t2g_cache.get_row({'thing1': False}))
print(t2g_cache.retrieve({'thing1': False}))

print(t2g_cache.retrieve({'thing2': True}))

t2g_cache.store({'thing2': True}, value={'cat': 'hat'})
print(t2g_cache.retrieve({'thing2': True}))

print(t2g_cache.get_row({'thing2': True}))
"""

####

from text2gene.cached import *

hgvs_text = 'NM_194248.1:c.158C>T'

"""
result = PubtatorCache.retrieve({'hgvs_text': hgvs_text})
if not result:
    result = pubtator_hgvs_to_pmid(hgvs_text)
    print('stored new result in cache:')
    PubtatorCache.store({'hgvs_text': hgvs_text}, result)
else:
    print('retrieved from cache:')

print(result)
"""

"""
pubquery = PubtatorCachedQuery()
pubquery.create_table()
print(pubquery.hgvs2pmid(hgvs_text))
"""

print(PubtatorHgvs2Pmid(hgvs_text))
print(ClinvarHgvs2Pmid(hgvs_text))
print(NCBIHgvs2Pmid(hgvs_text))


