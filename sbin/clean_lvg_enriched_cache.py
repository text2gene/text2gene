from text2gene import LVGEnriched

from text2gene.ncbi import NCBIEnrichedLVGCachedQuery

# This script was written to remove problematic entries from the ncbi_enriched_lvg_cache (entries that contained 
# unicode characters in the report.
#
# The real solution was to excise the .report attribute from the object, but since we wanted to keep the 
# cache entries we painstakingly built up, this was the workaround.
#
# This script can probably be safely removed from the repo, but remains "for now". --nm 3/28/2016


db = NCBIEnrichedLVGCachedQuery()

all_rows = db.fetchall('select * from ncbi_enriched_lvg_cache')
print(len(all_rows))

for row in all_rows:
    hgvs_text = row['cache_key'].strip()
    #print(hgvs_text)
    try:
        lex = LVGEnriched(hgvs_text)

    except ValueError as error:
        print('[%s] removing entry in cache (broken)' % hgvs_text)
        db.execute('delete from {} where cache_key="{}"'.format(db.tablename, hgvs_text))

    except UnicodeEncodeError:
        print('[%s] removing entry in cache (broken)' % hgvs_text)
        db.execute('delete from {} where cache_key="{}"'.format(db.tablename, hgvs_text))

