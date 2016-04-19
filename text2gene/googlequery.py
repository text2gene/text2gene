from __future__ import absolute_import, print_function, unicode_literals

import re
import logging
#import requests

from hgvs_lexicon import HgvsComponents, RejectedSeqVar, Variant

from .exceptions import Text2GeneError, GoogleQueryMissingGeneName

log = logging.getLogger('text2gene.googlequery')

# Google API Key authorized for Servers
API_KEY = 'AIzaSyBbzzCZbm5ccB6MC1e0y_tRFeNBdeoutPo'

# Google query API endpoint
CSE_URL = "https://www.googleapis.com/customsearch/v1"

# query example:
#  GET https://www.googleapis.com/customsearch/v1?key=INSERT_YOUR_API_KEY&cx=017576662512468239146:omuauf_lfve&q=lectures


def quoted_posedit(comp):
    posedit = '"%s"' % comp.posedit
    return posedit.replace('(', '').replace(')', '')


def get_posedits_for_seqvar(seqvar):
    posedits = []

    try:
        comp = HgvsComponents(seqvar)
    except RejectedSeqVar as error:
        log.debug(error)
        return []

    # 1) Official
    official_term = quoted_posedit(comp)
    if official_term:
        posedits.append(official_term)

    # 2) Slang
    try:
        for slang_term in comp.posedit_slang:
            slang_term = '"%s"' % slang_term
            if slang_term != official_term:
                posedits.append(slang_term)
    except NotImplementedError as error:
        # silently omit (but log) any seqvar with an edittype we don't currently support
        log.debug(error)

    return posedits


def get_posedits_for_lex(lex, seqtypes=['c', 'p', 'g', 'n']):
    """ The real Google Query Expansion workhorse behind the GoogleQuery object.

    Supply seqtypes argument to restrict query expansion to particular SequenceVariant type(s), e.g.:

        get_posedits_for_lex(lex, seqtypes=['p'])

    :param lex: *LVG* instance (HgvsLVG | NCBIEnrichedLVG | LVGEnriched | LVG object)
    :param seqtypes: list of strings indicating SequenceVariant "type" order [default: ['c', 'p', 'g', 'n']
    :returns: string containing expanded google query for variant
    """
    if not lex.gene_name:
        log.debug('No gene_name for SequenceVariant %s', lex.seqvar)
        return None

    used = set()
    posedits = []

    # start with the originating seqvar that created the LVG.
    if lex.seqvar.type in seqtypes:
        posedits = get_posedits_for_seqvar(lex.seqvar)
        for syn in posedits:
            used.add(syn)

    for seqtype in seqtypes:
        for seqvar in lex.variants[seqtype].values():
            try:
                for syn in get_posedits_for_seqvar(seqvar):
                    if syn not in used:
                        posedits.append(syn)
                        used.add(syn)
            except RejectedSeqVar as error:
                log.debug(error)

    return posedits


class GoogleQuery(object):

    GQUERY_TMPL = '"{gene_name}" {posedit_clause}'

    def __init__(self, lex=None, seqvar=None, hgvs_text=None, **kwargs):
        """ Requires either an LVG object (lex=) or a Sequence Variant object (seqvar=) or an hgvs_text string (hgvs_text=)

        Priority for instantiation (in case of multiple-parameter submission): lex, seqvar, hgvs_text

        Keywords:

            gene_name: should be supplied when instantiated with seqvar= or hgvs_text=
        """
        if lex:
            self.lex = lex
            self.seqvar = lex.seqvar
            self.hgvs_text = lex.hgvs_text

            if not lex.gene_name:
                self.gene_name = kwargs.get('gene_name', None)
            else:
                self.gene_name = lex.gene_name

        elif seqvar:
            self.lex = None
            self.seqvar = seqvar
            self.hgvs_text = '%s' % seqvar
            self.gene_name = kwargs.get('gene_name', None)

        elif hgvs_text:
            self.lex = None
            self.seqvar = Variant(hgvs_text)
            self.hgvs_text = hgvs_text
            self.gene_name = kwargs.get('gene_name', None)

        if self.gene_name is None:
            raise GoogleQueryMissingGeneName('Information supplied with variant %s is missing gene name.' % self.seqvar)

        self.synonyms = {'c': [], 'g': [], 'p': [], 'n': []}

    @staticmethod
    def _count_terms_in_term(term):
        if term is None or term.strip() == '':
            return 0

        term = re.sub('[+\->\/]+', ' ', term)
        return len(term.strip().split())

    def _query_seqtype(self, seqtype, term_limit):
        if not self.lex:
            if self.seqvar.type != seqtype:
                return None
        return self.build_query(seqtype, term_limit)

    def query_c(self, term_limit=31):
        """ Generate string query from instantiating information for HGVS c. DNA variants only. """
        return self._query_seqtype(seqtype='c', term_limit=term_limit)

    def query_p(self, term_limit=31):
        """ Generate string query from instantiating information for HGVS p. protein variants only. """
        return self._query_seqtype(seqtype='p', term_limit=term_limit)

    def query_g(self, term_limit=31):
        """ Generate string query from instantiating information for HGVS g. DNA variants only. """
        return self._query_seqtype(seqtype='g', term_limit=term_limit)

    def query_n(self, term_limit=31):
        """ Generate string query from instantiating information for HGVS n. RNA variants only. """
        return self._query_seqtype(seqtype='n', term_limit=term_limit)

    def build_query(self, seqtypes=['c', 'p', 'g', 'n'], term_limit=31):
        """ Generate string query from instantiating information.

        Max term limit set to 31 by default, since Google cuts off queries at 32 terms.

        Note that Google counts lexemes separated by special characters as multiple terms,
        so "6-8dupT" is counted as 2 terms.  "+6-8dupT" would be 2 terms as well (the "+"
        is effectively ignored).

        :param term_limit: (int) max number of synonyms to return in built query
        :return: (str) built query
        """
        if self.lex:
            posedits = get_posedits_for_lex(self.lex, seqtypes)
        else:
            posedits = get_posedits_for_seqvar(self.seqvar)

        # Count how many terms Google will ding us for.
        terms = []
        term_count = 0

        for posedit in posedits:
            if term_count == term_limit:
                break
            terms.append(posedit)
            term_count += self._count_terms_in_term(posedit)

        posedit_clause = '(%s)' % '|'.join(terms)
        return self.GQUERY_TMPL.format(gene_name=self.gene_name, posedit_clause=posedit_clause)

    def __str__(self):
        return self.build_query()


if __name__ == '__main__':
    test_sub = "NM_014874.3:c.891C>T"
    sub_expected = '"MFN2" ("891C>T"|"891C->T"|"891C-->T"|"891C/T"|"C891T"|"1344C>U"|"1344C->U"|"1344C-->U"|"1344C/U"|"C1344U")'

    test_del = 'NM_007294.3:c.4964_4982delCTGGCCTGACCCCAGAAGA'
    del_expected = '"BRCA1" ("4964_4982delCTGGCCTGACCCCAGAAGA"|"4964_4982del"|"5196_5214delCUGGCCUGACCCCAGAAGA"|"5196_5214del"|"Ser1655TyrfsTer16"|"4823_4841delCTGGCCTGACCCCAGAAGA"|"4823_4841del"|"5104_5122delCUGGCCUGACCCCAGAAGA"|"5104_5122del"|"Ser1608TyrfsTer16"|"1652_1670delCTGGCCTGACCCCAGAAGA"|"1652_1670del"|"1846_1864delCUGGCCUGACCCCAGAAGA"|"1846_1864del"|"Ser551TyrfsTer16"|"1671_1689delCUGGCCUGACCCCAGAAGA"|"1671_1689del"|"5027_5045delCTGGCCTGACCCCAGAAGA"|"5027_5045del"|"5259_5277delCUGGCCUGACCCCAGAAGA"|"5259_5277del"|"Ser1676TyrfsTer16")'

    test_dup = 'NM_025114.3:c.6869dupA'
    dup_expected = '"CEP290" ("6869dupA"|"6869dup"|"7213dupA"|"7213dup"|"Asn2290LysfsTer6")'
