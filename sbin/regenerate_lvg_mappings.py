
from text2gene.lvg_cached import LVG, HgvsLVGCached

db = HgvsLVGCached()
all_rows = db.fetchall('select * from hgvslvg_cache')

for row in all_rows:
    hgvs_text = row['cache_key'].strip()
    lex = LVG(hgvs_text, force_granular=True)
    print(lex)

