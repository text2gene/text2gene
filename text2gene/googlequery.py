from __future__ import absolute_import, print_function, unicode_literals

import re
import logging
import urllib

import requests

from metapub.urlreverse import UrlReverse
from metapub.convert import doi2pmid
from metapub.exceptions import MetaPubError 

from medgen.annotate.gene import GeneSynonyms
from hgvs_lexicon import HgvsComponents, RejectedSeqVar, Variant

from .exceptions import Text2GeneError, GoogleQueryMissingGeneName, GoogleQueryRemoteError

log = logging.getLogger('text2gene.googlequery')

# Google API Key authorized for Servers
API_KEY = 'AIzaSyBbzzCZbm5ccB6MC1e0y_tRFeNBdeoutPo'

# Google query API endpoint
CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Google CSE engine ID ("cx") -- whitelisted journals (list of relevant science publishers, NIH, etc)
CSE_CX_WHITELIST = '003914143621252222636:gtzu3oichua'

# Google CSE engine ID ("cx") -- whitelisted schemas (ScholarlyArticle only)
CSE_CX_SCHEMA = '003914143621252222636:-mop04_esug'

# Google CSE query templates -- one per engine.
CSE_QUERY_TEMPLATES = {'whitelist': CSE_URL + '?key=' + API_KEY + '&cx=' + CSE_CX_WHITELIST + '&q={}',
                        'schema': CSE_URL + '?key=' + API_KEY + '&cx=' + CSE_CX_SCHEMA + '&q={}',
                       }


def query_cse_return_response(qstring, cse='whitelist', start_index=None):
    """ Query the Google Custom Search Engine for provided query string.

    :param qstring: (str)
    :param cse: (str) name of preconfigured CSE ('whitelist' or 'schema') [default: 'whitelist']
    :return response: (dict) Google CSE response to query.
    """
    if start_index:
        query = CSE_QUERY_TEMPLATES[cse].format(qstring) + '&start=%i' % start_index
    else:
        query = CSE_QUERY_TEMPLATES[cse].format(qstring)

    response = requests.get(query)

    if not response.ok:
        raise GoogleQueryRemoteError('Google CSE query returned not-ok state: %i (query string: %s)' % (response.status_code, query))
    return response.json()


class GoogleCSEResult(object):

    def __init__(self, item, **kwargs):
        # item
        self.title = item.get('title', None)
        self.url = item.get('link', None)

        if self.url:
            self.url = urllib.unquote_plus(self.url)

        self.mime = item.get('mime', None)
        self.snippet = item.get('snippet', None)
        self.htmlSnippet = item.get('htmlSnippet', None)
        self.title = item.get('title', None)
        self.htmlTitle = item.get('htmlTitle', None)

        # attributes that may or may not be filled in by the item dict
        self.doi = None
        self.citation_title = None
        self.metatags = None

        # PMID attribute will hopefully become filled by some means...
        self.pmid = None

        # Inspect the dictionary and fill what variables we find.
        self._fill_variables_from_cse_result(item)

        # Now try to get the PMID!
        if not self.doi:
            self.urlreverse = UrlReverse(self.url)
            self.doi = self.urlreverse.doi
            self.pmid = self.urlreverse.pmid

        else:
            self.urlreverse = None
            try:
                self.pmid = doi2pmid(self.doi)
            except MetaPubError as error:
                log.debug(error)
                self.pmid = None

        # coerce to int if we got one.
        try:
            self.pmid = int(self.pmid)
        except (ValueError, TypeError):
            log.debug('PMID was a monster! Got %s (doi: %s) (url: %s)' % (self.pmid, self.doi, self.url))
            self.pmid = None

    def to_dict(self):
        return {'url': self.url,
                'pmid': self.pmid,
                'mime': self.mime,
                'snippet': self.snippet,
                'htmlSnippet': self.htmlSnippet,
                'doi': self.doi,
                'citation_title': self.citation_title,
                'title': self.title,
                'htmlTitle': self.htmlTitle,
                }

    def _fill_variables_from_cse_result(self, item):
        if item.get('pagemap', None):
            if item['pagemap'].get('metatags', None):
                self.metatags = item['pagemap']['metatags']
                for tag in item['pagemap']['metatags']:
                    if tag.get('citation_doi'):
                        self.doi = tag['citation_doi'].replace('doi:', '')
                    if tag.get('citation_title'):
                        self.citation_title = tag['citation_title']


def parse_cse_items(cse_items):
    """ Extract important pieces of information from Google CSE query results.

    :param cse_items: list of dictionaries
    :return: list of GoogleCSEResult objects
    """
    reslist = []
    for item in cse_items:
        reslist.append(GoogleCSEResult(item))
    return reslist


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


def get_posedits_for_lex(lex, seqtypes=None):
    """ The real Google Query Expansion workhorse behind the GoogleQuery object.

    Supply seqtypes argument to restrict query expansion to particular SequenceVariant type(s), e.g.:

        get_posedits_for_lex(lex, seqtypes=['p'])

    :param lex: *LVG* instance (HgvsLVG | NCBIEnrichedLVG | LVGEnriched | LVG object)
    :param seqtypes: list of strings indicating SequenceVariant "type" order [default: ['c', 'p', 'g', 'n']
    :returns: string containing expanded google query for variant
    """
    if not seqtypes:
        seqtypes = ['c', 'p', 'g', 'n']

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

    GQUERY_TMPL = '{gene_name} {posedit_clause}'

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
        self.gene_synonyms = GeneSynonyms(self.gene_name)

        # choice of Google CSE ("cx") -- "whitelist" or "schema" [default: whitelist]
        self.cse = kwargs.get('cse', 'whitelist')

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

    def build_query(self, seqtypes=None, term_limit=31, use_gene_synonyms=True):
        """ Generate string query from instantiating information.

        Max term limit set to 31 by default, since Google cuts off queries at 32 terms.

        Note that Google counts lexemes separated by special characters as multiple terms,
        so "6-8dupT" is counted as 2 terms.  "+6-8dupT" would be 2 terms as well (the "+"
        is effectively ignored).

        :param seqtypes: (list) one-letter strings indicating priority order of sequence types to use for query
        :param term_limit: (int) max number of synonyms to return in built query
        :param use_gene_synonyms: (bool) [default: True]
        :return: (str) built query
        """
        if not seqtypes:
            seqtypes = ['c', 'p', 'g', 'n']

        if self.lex:
            posedits = get_posedits_for_lex(self.lex, seqtypes)
        else:
            posedits = get_posedits_for_seqvar(self.seqvar)

        # Count how many terms Google will ding us for.
        terms = []
        term_count = 0

        for posedit in list(posedits):
            if term_count == term_limit:
                break
            terms.append(posedit)
            term_count += self._count_terms_in_term(posedit)

        posedit_clause = '(%s)' % '|'.join(terms)
        if use_gene_synonyms and self.gene_synonyms != []:
            gene_clause = '(%s)' % '|'.join('"%s"' % gene for gene in self.gene_synonyms)
            return self.GQUERY_TMPL.format(gene_name=gene_clause, posedit_clause=posedit_clause)
        else:
            return self.GQUERY_TMPL.format(gene_name=self.gene_name, posedit_clause=posedit_clause)

    def send_query(self, qstring=None, seqtypes=None, pages=1):
        """ Sends query to the Google Custom Search Engine specified in this object's 'cse' attribute
        ('whitelist' by default).  Any arbitrary `qstring` can be supplied; if not supplied, this function
        composes a query string using self.build_query(), informed by the optional `seqtypes` parameter
        (default: all seqtypes).

        This function retrieves up to `pages` of Google CSE results (default: 1).

        :param qstring: (str)
        :param seqtypes: (list)
        :param pages: (int)
        :return: list of CSEResult items (or empty list if no results)
        """
        if seqtypes is None:
            seqtypes = ['c', 'p', 'g', 'n']
        if qstring is None:
            qstring = self.build_query(seqtypes=seqtypes)

        cse_results = []
        response = query_cse_return_response(qstring=qstring, cse=self.cse)
        num_results = int(response['queries']['request'][0]['totalResults'])
        if num_results != 0:
            cse_results = cse_results + parse_cse_items(response['items'])
            # generate start_index in series like [11, 21, 31]
            for start_index in range(11, pages * 10 + 1, 10):
                try:
                    cse_results = cse_results + parse_cse_items(response['items'])
                except KeyError:
                    break

        return cse_results

    def __str__(self):
        return self.build_query()
