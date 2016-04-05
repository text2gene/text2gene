
import unittest

from text2gene.lvg_cached import HgvsLVGCached
from text2gene import LVG

test_hgvs_c = 'NM_001232.3:c.919G>C'

lvg_cache_db = HgvsLVGCached()

class TestHgvsLVGCached(unittest.TestCase):

    def setUp(self):
        lvg_cache_db.delete(test_hgvs_c)

    def tearDown(self):
        pass

    def test_LVG_cache(self):
        lex = LVG(test_hgvs_c)
        result = lvg_cache_db.retrieve(test_hgvs_c)
        assert result is not None

    #def test_LVG_granular(self):
    #    lex = LVG(test_hgvs_c)

