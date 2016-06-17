
import unittest

from metavariant import VariantLVG
from metavariant.exceptions import CriticalHgvsError

class TestVariantLVG(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_del_numeric_or_chars(self):
        hgvs_text = 'NM_005228.3:c.2240_2257del18'
        lex = VariantLVG(hgvs_text)

        expected_c = [
                "NM_005228.3:c.2240_2257del18",
                "NM_005228.3:c.2240_2257delTAAGAGAAGCAACATCTC"
                ]
        expected_g = 'NC_000007.13:g.55242470_55242487delTAAGAGAAGCAACATCTC'
        expected_p = 'NP_005219.2:p.(Leu747_Pro753delinsSer)'
        expected_n = 'NM_005228.3:n.2486_2503delTAAGAGAAGCAACATCTC'

        for c_hgvs_text in expected_c:
            assert c_hgvs_text in lex.hgvs_c

        assert expected_g in lex.hgvs_g
        assert expected_n in lex.hgvs_n
        assert expected_p in lex.hgvs_p
    
    def test_plain_lvgno_variant_mappings(self):
        #TODO
        hgvs_text = 'NM_194248.1:c.158C>T'

    def test_bad_hgvs_text_raises_CriticalHgvsError(self):
        bad_hgvs_text = 'NM_004628.4:c.621_622ins83'
    
        with self.assertRaises(CriticalHgvsError):
            VariantLVG(bad_hgvs_text)

    def test_gene_name(self):
        hgvs_text = 'NM_000548.3:c.826_827del'
        lex = VariantLVG(hgvs_text)
        assert lex.gene_name == 'TSC2'

