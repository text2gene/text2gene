from __future__ import absolute_import, print_function, unicode_literals

import re
import os
import logging
import urllib
import hashlib

import requests

from metapub import UrlReverse
from metapub.convert import doi2pmid

from medgen.annotate.gene import GeneSynonyms
from metavariant import VariantComponents, Variant
from metavariant.exceptions import RejectedSeqVar

from .exceptions import GoogleQueryMissingGeneName, GoogleQueryRemoteError
from .sqlcache import SQLCache
from .config import GRANULAR_CACHE, CONFIG

log = logging.getLogger('text2gene.googlequery')

# disable noisy SSL warnings arising from improperly configured remote websites
# (a necessary evil, sadly)
from requests.packages import urllib3
urllib3.disable_warnings()

# Google API Key authorized for Servers
API_KEY = CONFIG.get('google', 'api_key')

# Google query API endpoint
CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Google CSE engine ID ("cx") -- whitelisted journals (list of relevant science publishers, NIH, etc)
#CSE_CX_WHITELIST = '003914143621252222636:gtzu3oichua'
CSE_CX_WHITELIST = '009155410218757639293:nyh3tdzvfhc'

# Google CSE engine ID ("cx") -- whitelisted schemas (ScholarlyArticle only)
CSE_CX_SCHEMA = '003914143621252222636:-mop04_esug'

# Google CSE query templates -- one per engine.
CSE_QUERY_TEMPLATES = {'whitelist': CSE_URL + '?key=' + API_KEY + '&cx=' + CSE_CX_WHITELIST + '&q={}',
                        'schema': CSE_URL + '?key=' + API_KEY + '&cx=' + CSE_CX_SCHEMA + '&q={}',
                       }

# define "all" seqtypes for search purposes as using the following set (notably absent the g.DNA seqtype,
#       which we have proven experimentally to not help much (or at all) in finding pubmed evidence).
ALL_SEQTYPES = ['c', 'p', 'n']

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

    TYPES_WE_DONT_LIKE = ['xslt', 'xlsx', 'csv']

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

        # UrlReverse container
        self.urlreverse = None

        # In case we run into a problem loading UrlReverse, or we want to log an invalid filetype.
        self.error = None

        # PMID attribute will hopefully become filled by some means...
        self.pmid = None

        # Inspect the dictionary and fill what variables we find.
        self._fill_variables_from_cse_result(item)

        # if this an Excel spreadsheet it can fuck right off. See T2G-73
        path = urllib.urlparse(self.url).path
        ext = os.path.splitext(path)[1]
        if ext in self.TYPES_WE_DONT_LIKE:
            self.error = 'Ignoring unwanted filetype "{ext}" from result {url}'.format(ext=ext, url=self.url)
            log.debug(self.error)
            return

        # Now try to get the PMID!
        if not self.doi:
            try:
                self.urlreverse = UrlReverse(self.url, verify=False)    # "verify" is an extra step we don't really need.
                self.doi = self.urlreverse.doi
                self.pmid = self.urlreverse.pmid
            except Exception as error:
                self.urlreverse = None
                self.error = '%r' % error
        else:
            try:
                self.pmid = doi2pmid(self.doi)
            except Exception as error:
                # so far we've seen XMLSyntaxError and MetaPubError...
                self.error = '%r' % error
                self.pmid = None

        # coerce to int if we got one.
        try:
            self.pmid = int(self.pmid)
        except (ValueError, TypeError):
            log.debug('PMID lookup failed for {url} (doi: {doi})'.format(doi=self.doi, url=self.url))
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
                'urlreverse': None if not self.urlreverse else self.urlreverse.to_dict(),
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

    def __str__(self):
        out = 'Link: %s\n' % self.url
        out += '  PMID: %r\n' % self.pmid
        out += '  DOI: %r\n' % self.doi
        if self.urlreverse:
            out += '  Steps:\n'
            for step in self.urlreverse.steps:
                out += '\t * %s\n' % step
        return out

    def __repr__(self):
        return '<text2gene.googlequery.GoogleCSEResult:%s (pmid: %r) (doi: %r)>' % (self.url, self.pmid, self.doi)


def parse_cse_items(cse_items):
    """ Convert list of Google CSE "items" into list of GoogleCSEResult objects.

    :param cse_items: list of dictionaries
    :return: list of GoogleCSEResult objects
    """
    reslist = []
    for item in cse_items:
        reslist.append(GoogleCSEResult(item))
    return reslist


def googlecse2pmid(cse_results):
    """ Given a list of GoogleCSEResult items, return a list of the unique PMIDs found.

    :param cse_results: (list)
    :return: list of PMIDs or empty list
    """
    pmids = set()
    for cseres in cse_results:
        if cseres.pmid:
            pmids.add(cseres.pmid)
    return list(pmids)


def quoted_posedit(comp):
    posedit = '"%s"' % comp.posedit
    return posedit.replace('(', '').replace(')', '')


def get_posedits_for_seqvar(seqvar):
    posedits = []

    try:
        comp = VariantComponents(seqvar)
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

    :param lex: *LVG* instance (VariantLVG | NCBIEnrichedLVG | LVGEnriched | LVG object)
    :param seqtypes: list of strings indicating SequenceVariant "type" order [default: ['c', 'p', 'g', 'n']
    :returns: string containing expanded google query for variant
    """
    if not seqtypes:
        seqtypes = ALL_SEQTYPES

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


class GoogleCSEngine(object):

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
            if lex.gene_name:
                self.gene_name = lex.gene_name
            else:
                self.gene_name = kwargs.get('gene_name', None)

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

        # self.synonyms = {'c': [], 'g': [], 'p': [], 'n': []}
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
            seqtypes = ALL_SEQTYPES

        if self.lex:
            posedits = get_posedits_for_lex(self.lex, seqtypes)
        else:
            posedits = get_posedits_for_seqvar(self.seqvar)

        # Count how many terms Google will ding us for.
        # Reject any posedits that are longer than 100 chars (Google won't accept them.)
        terms = []
        term_count = 0

        for posedit in list(posedits):
            if len(posedit) > 100:
                break
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

    def send_query(self, qstring=None, seqtypes=None, pages=2):
        """ Sends query to the Google Custom Search Engine specified in this object's 'cse' attribute
        ('whitelist' by default).  Any arbitrary `qstring` can be supplied; if not supplied, this function
        composes a query string using self.build_query(), informed by the optional `seqtypes` parameter
        (default: all seqtypes).

        This function retrieves up to `pages` of Google CSE results (default: 2).

        :param qstring: (str)
        :param seqtypes: (list)
        :param pages: (int)
        :return: list of dictionaries
        """
        if seqtypes is None:
            seqtypes = ALL_SEQTYPES

        if qstring is None:
            qstring = self.build_query(seqtypes=seqtypes)

        response = query_cse_return_response(qstring=qstring, cse=self.cse)
        num_results = int(response['queries']['request'][0]['totalResults'])
        items = []

        if num_results != 0:
            items = response['items']
            for start_index in range(11, pages * 10 + 1, 10):
                if start_index > num_results:
                    break
                response = query_cse_return_response(qstring, start_index=start_index)
                items = items + response.get('items', [])
        return items

    def __str__(self):
        return self.build_query()


class GoogleCachedQuery(SQLCache):

    """ Represents a single cached event of querying Google with configurable parameters
    (lex, seqtypes, term_limit, use_gene_synonyms

    Stores results in cache as md5(qstring) -> json result
    """
    VERSION = 0

    def __init__(self, granular=False, granular_table='google_match'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('google_query')

    def _truncate_result(self, result):
        """ Removes unnecessary bulk from Google CSE result list. """
        out = []
        for item in result:
            if type(item) == dict:
                if item.get('pagemap', None):
                    for key in ('person', 'article', 'cse_thumbnail'):
                        if item['pagemap'].get(key, None):
                            item['pagemap'].pop(key)
        out.append(item)
        return out

    def get_cache_key(self, qstring):
        """ Returns a cache_key for the supplied Google query string.

        :param qstring: (str) Google query string
        :return: md5 hash of query string
        """
        return hashlib.md5(qstring).hexdigest()

    def store_granular(self, hgvs_text, cse_results):
        pmids = googlecse2pmid(cse_results)
        if pmids:
            entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in pmids]
            self.batch_insert(self.granular_table, entry_pairs)

    def query(self, lex, seqtypes=None, term_limit=31, use_gene_synonyms=True, skip_cache=False, force_granular=False):
        """ Supply a "lex" object to run a GoogleQuery and return all parseable results as GoogleCSEResult
        objects.  Supply seqtypes as a list of sequence types to constrain query as desired.

        Examples:
            GoogleQuery(lex, seqtypes=['c','p'], use_gene_synonyms=False)


        :param lex: any lexical variant object (VariantLVG, NCBIEnrichedLVG, NCBIHgvsLVG)
        :param seqtypes: list of seqtypes [default: ALL_SEQTYPES global]
        :param term_limit: (int) number of terms to constrain query to [default: 31]
        :param use_gene_synonyms: (bool) whether to use GeneSynonyms in query [default: True]
        :param skip_cache: whether to force reloading the data by skipping the cache
        :return: list of GoogleCSEresult objects or empty list if no results
        """
        if seqtypes is None:
            seqtypes = ALL_SEQTYPES

        gcse = GoogleCSEngine(lex)
        qstring = gcse.build_query(seqtypes, term_limit=term_limit, use_gene_synonyms=use_gene_synonyms)

        # This looks like a lot of extra steps (get the results, parse the results, convert the results
        # into PMIDs)... but there's an advantage. By storing the JSON response instead of the GoogleCSEResult
        # objects, we have the power to potentially return better GoogleCSEResult objects at a later time -- i.e.
        # whenever metapub's UrlReverse improves at PMID resolution.
        #
        # In other words, we can reuse our cached API results for each query while leaving ourselves open to the
        # possibility of taking advantage of improved interpretation over time.

        if not skip_cache:
            result = self.retrieve(qstring, version=self.VERSION)
            if result is not None:
                log.debug('GoogleQuery: loaded results from cache for qstring %s' % qstring)
                cse_results = parse_cse_items(result)
                if force_granular:
                    self.store_granular(lex.hgvs_text, cse_results)
                return cse_results

        log.debug('GoogleQuery: Hitting Google API with qstring %s' % qstring)
        result = gcse.send_query(qstring)

        # if result is too long to be stored, doctor it up (remove unnecessary parts):
        if len('%r' % result) > 64000:
            result = self._truncate_result(result)

        self.store(qstring, result)

        cse_results = parse_cse_items(result)

        if (force_granular or self.granular) and result:
            self.store_granular(lex.hgvs_text, cse_results)

        return cse_results

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for GoogleCachedQuery'.format(tname))

        self.execute("drop table if exists {}".format(tname))

        sql = """create table {} (
                  hgvs_text varchar(255) not null,
                  PMID int(11) default NULL,
                  version int(11) default NULL)
                  ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)
        sql = 'call create_index("{}", "hgvs_text,PMID")'.format(tname)
        self.execute(sql)


GoogleQuery = GoogleCachedQuery(granular=GRANULAR_CACHE).query
