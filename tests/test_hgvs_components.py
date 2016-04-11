from __future__ import absolute_import, print_function, unicode_literals

import unittest

from hgvs_lexicon import Variant, HgvsComponents

from hgvs_lexicon.hgvs_samples import hgvs_c, hgvs_g, hgvs_p, hgvs_n


class TestHgvsComponents(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_substitution(self):
        var_c = Variant(hgvs_c['SUB'])
        comp = HgvsComponents(var_c) 
        pass

    def test_deletion(self):
        var_g = Variant(hgvs_g['DEL'])
        comp = HgvsComponents(var_g)
        pass

    def test_frameshift(self):
        var_p = Variant(hgvs_p['FS'])
        comp = HgvsComponents(var_p)
        pass
    
    def test_indel(self):
        var_n = Variant(hgvs_n['INDEL'])
        comp = HgvsComponents(var_n)
        pass

    def test_duplication(self):
        var_c = Variant(hgvs_c['DUP'])
        comp = HgvsComponents(var_c)
        pass

    def test_insert(self):
        var_c = Variant(hgvs_c['INS'])
        comp = HgvsComponents(var_c)
        pass
    


