
import unittest

from text2gene.lvg_cached import VariantLVGCached
from text2gene.ncbi import NCBIEnrichedLVGCachedQuery
from text2gene import LVG, LVGEnriched

test_hgvs_c = 'NM_001232.3:c.919G>C'
test_hgvs_n = 'NM_194248.2:n.285C>T'

lvg_cache_db = VariantLVGCached()
ncbi_lvg_cache_db = NCBIEnrichedLVGCachedQuery()

class TestVariantLVGCached(unittest.TestCase):

    def setUp(self):
        lvg_cache_db.delete(test_hgvs_c)

    def tearDown(self):
        pass

    def test_LVG_cache(self):
        lex = LVG(test_hgvs_c)
        result = lvg_cache_db.retrieve(test_hgvs_c)
        assert result is not None

        lex = LVG(test_hgvs_c)
        assert lex.hgvs_text == test_hgvs_c

    def test_ncbi_enriched_lvg_cache(self):
        ncbi_lvg_cache_db.delete(test_hgvs_n)
        lex = LVGEnriched(test_hgvs_n)
        result = ncbi_lvg_cache_db.retrieve(test_hgvs_c)
        assert result is not None

        lex = LVGEnriched(test_hgvs_n)
        assert lex.hgvs_text == test_hgvs_n
        
    #def test_LVG_granular(self):
    #    lex = LVG(test_hgvs_c)

