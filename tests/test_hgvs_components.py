from __future__ import absolute_import, print_function, unicode_literals

import unittest

from metavariant import Variant, VariantComponents

from metavariant.hgvs_samples import hgvs_c, hgvs_g, hgvs_p, hgvs_n


class TestVariantComponents(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_substitution(self):
        var_c = Variant(hgvs_c['SUB'])
        comp = VariantComponents(var_c) 
        pass

    def test_deletion(self):
        var_g = Variant(hgvs_g['DEL'])
        comp = VariantComponents(var_g)
        pass

    def test_frameshift(self):
        var_p = Variant(hgvs_p['FS'])
        comp = VariantComponents(var_p)
        pass
    
    def test_indel(self):
        var_n = Variant(hgvs_n['INDEL'])
        comp = VariantComponents(var_n)
        pass

    def test_duplication(self):
        var_c = Variant(hgvs_c['DUP'])
        comp = VariantComponents(var_c)
        pass

    def test_insert(self):
        var_c = Variant(hgvs_c['INS'])
        comp = VariantComponents(var_c)
        pass
    


