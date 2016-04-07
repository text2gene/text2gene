from __future__ import absolute_import, print_function, unicode_literals

import unittest

from text2gene.api import GoogleQuery, 

from .hgvs_examples import supported_edittypes, hgvs_c, hgvs_g, hgvs_p, hgvs_n


class TestGoogleQuery(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_substitution_case(self):
        var_c = Variant(hgvs_c['SUB'])
    
        pass

    def test_deletion_case(self):
        var_c = Variant(hgvs_c['DEL'])
        pass

    def test_frameshift_case(self):
        var_c = Variant(hgvs_c['FS'])
        pass
    
    def test_indel_case(self):
        var_c = Variant(hgvs_c['INDEL'])
        pass

    def test_dup_case(self):
        var_c = Variant(hgvs_c['DUP'])
        pass

    def test_ins_case(self):
        var_c = Variant(hgvs_c['INS'])
        pass

    def test_dup_intronic(self):
        hgvs_text = "NM_000722.2:c.355-5dupT"
        query = GoogleQuery(hgvs_text)
        assert query == '"CACNA2D1" ("355-5dupT"|"355-5dup"|"611-5dupU"|"611-5dup")'

