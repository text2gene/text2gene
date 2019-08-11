import logging

from metavariant import Variant
from text2gene.sqlcache import SQLCache

sample_sheet = open('data/clinvar_epilepsy_2944.tsv').read().split('\n')
LOADED_EXAMPLES = []
for line in sample_sheet:
    try:
        seqvar = Variant(line.split()[0])
    except Exception as error:
        print(error)
        continue

    if seqvar:
        LOADED_EXAMPLES.append('%s' % seqvar)

db = SQLCache('dummy')
index = 0
for sample in LOADED_EXAMPLES:
    index += 1
    row = db.fetchrow('select * from ncbi_enriched_lvg_cache where cache_key="%s"' % sample)
    if row:
        print(index, 'deleting', row['cache_key'])
        db.execute('delete from ncbi_enriched_lvg_cache where cache_key="%s"' % sample)
    else:
        print(index, 'no row for %s' % sample)


