from text2gene import LVGEnriched

from text2gene.ncbi import NCBIEnrichedLVGCachedQuery


db = NCBIEnrichedLVGCachedQuery()

all_rows = db.fetchall('select * from ncbi_enriched_lvg_cache')

for row in all_rows:
    hgvs_text = row['cache_key'].strip()
    try:
        lex = LVGEnriched(hgvs_text)

    except UnicodeEncodeError:
        print('[%s] removing entry in cache (broken)' % hgvs_text)
        db.execute('delete from {} where cache_key="{}"'.format(db.tablename, hgvs_text))

