from __future__ import absolute_import, print_function, unicode_literals

import unittest

from hgvs_lexicon.hgvs_samples import *
from hgvs_lexicon import Variant

from text2gene.api import GoogleQuery, LVG, LVGEnriched

class TestGoogleQuery(unittest.TestCase):

    def setUp(self):
        self.test_lex = LVGEnriched('NM_000125.3:c.1339_1340delTGinsGC')
        self.test_gq = GoogleQuery(self.test_lex) 

    def tearDown(self):
        pass

    def test_query_c(self):
        assert self.test_gq.query_c() == '"ESR1" ("1339_1340delTGinsGC"|"1345_1346delTGinsGC"|"1336_1337delTGinsGC")' 

    def test_query_g(self):
        assert self.test_gq.query_g() == '"ESR1" ("152382229_152382230delTGinsGC")'

    def test_query_p(self):
        assert self.test_gq.query_p() == '"ESR1" ("Cys447Ala"|"C447A"|"Cys446Ala"|"C446A"|"Cys449Ala"|"C449A")'

    def test_query_n(self):
        assert self.test_gq.query_n() == '"ESR1" ("1600_1601delTGinsGC"|"1557_1558delTGinsGC"|"1573_1574delTGinsGC"|"1563_1564delTGinsGC"|"1709_1710delTGinsGC"|"1554_1555delTGinsGC")'

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
        
