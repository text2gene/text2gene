
import unittest

from text2gene.lvg_cached import VariantLVGCached
from text2gene import LVG

test_hgvs_c = 'NM_001232.3:c.919G>C'
test_hgvs_n = 'NM_194248.2:n.285C>T'

lvg_cache_db = VariantLVGCached()

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

