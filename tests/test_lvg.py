
import unittest

from hgvs_lexicon import HgvsLVG



class TestHgvsLVG(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_del_numeric_or_chars(self):
        hgvs_text = 'NM_005228.3:c.2240_2257del18'
        lex = HgvsLVG(hgvs_text)

        expected_c = [
                "NM_005228.3:c.2240_2257del18",
                "NM_005228.3:c.2240_2257delTAAGAGAAGCAACATCTC"
                ]
        expected_g = 'NC_000007.13:g.55242470_55242487delTAAGAGAAGCAACATCTC'
        expected_p = 'NP_005219.2:p.(Leu747_Pro753delinsSer)'
        expected_n = 'NM_005228.3:n.2486_2503delTAAGAGAAGCAACATCTC'

        for c_hgvs_text in expected_c:
            assert c_hgvs_text in lex.hgvs_c_variants

        assert expected_g in lex.hgvs_g_variants
        assert expected_n in lex.hgvs_n_variants
        assert expected_p in lex.hgvs_p_variants

    
    def test_no_variant_mappings(self):
        hgvs_text = 'NM_194248.1:c.158C>T'

