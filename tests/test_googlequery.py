from __future__ import absolute_import, print_function, unicode_literals

import unittest

from hgvs_lexicon.hgvs_samples import *
from hgvs_lexicon import Variant

from text2gene.api import GoogleQuery, LVG, LVGEnriched

class TestGoogleQuery(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_substitution_case(self):
        var_c = Variant(hgvs_c['SUB'])
        lex = LVG(var_c)
        query = GoogleQuery(lex).build_query()
        assert query.startswith('"SCN5A" ("4786T>A"|"T4786A"|"4786T-->A"|"4786T/A"|"4786T->A"')
        assert query.find('4732T->A') > -1
        assert query.find('4783T-->A') > -1
        #assert query.find(

    def test_deletion_case(self):
        var_c = Variant(hgvs_c['DEL'])
        lex = LVG(var_c)
        query = GoogleQuery(lex).build_query()

    def test_frameshift_case(self):
        var_c = Variant(hgvs_c['FS'])
        lex = LVG(var_c)
        query = GoogleQuery(lex).build_query()
    
    def test_indel_case(self):
        var_c = Variant(hgvs_c['INDEL'])
        lex = LVG(var_c)
        query = GoogleQuery(lex).build_query()

    def test_dup_case(self):
        var_c = Variant(hgvs_c['DUP'])
        lex = LVG(var_c)
        query = GoogleQuery(lex).build_query()

    def test_ins_case(self):
        var_c = Variant(hgvs_c['INS'])
        lex = LVG(var_c)
        query = GoogleQuery(lex).build_query()

    def test_dup_intronic(self):
        hgvs_text = "NM_000722.2:c.355-5dupT"
        lex = LVG(hgvs_text)
        query = GoogleQuery(lex).build_query()
        assert query.startswith('"CACNA2D1" ("355-5dupT"|"355-5dup"|"355-14dupT"|"355-14dup"')

    def test_no_duplicate_terms_in_query(self):
        hgvs_text = "NM_000722.2:c.355-5dupT"
        lex = LVG(hgvs_text)
        query = GoogleQuery(lex).build_query()
        posedits = query.strip('"CACNA2D1" (').strip(')').split('|')
        assert len(posedits) == len(set(posedits))
        
