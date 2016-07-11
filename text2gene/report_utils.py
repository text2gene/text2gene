from __future__ import absolute_import, unicode_literals

import logging

from medgen.api import ClinvarVariationID, ClinVarDB
from medgen.api import GeneID, GeneName

from metapub import PubMedFetcher, FindIt

from flask import Markup

from .googlequery import GoogleQuery, GoogleCSEngine
from .exceptions import NCBIRemoteError, GoogleQueryMissingGeneName, GoogleQueryRemoteError
from .ncbi import NCBIHgvs2Pmid
from .cached import ClinvarHgvs2Pmid
from .pmid_lookups import pubtator_results_for_lex

log = logging.getLogger('text2gene')

fetch = PubMedFetcher()

GENEREVIEWS_URL = 'http://www.ncbi.nlm.nih.gov/books/{bookid}/'


class CitationTable(object):
    """ Given an LVG object ("lex"), collect citations from all specified functions, configurable
    through keyword arguments.

    By default, all available search modules are used.  They can be disabled by supplying
    <search_module_name> = False at instantiation.  Available modules:

        * clinvar
        * ncbi
        * pubtator
        * google

    Citations are keyed to PMID via the .pmid2citation attribute, i.e.:
        {<pmid>: <Citation instance>}

    The magic .citations property returns a flat list of Citations sorted by PMID, highest-numbered
    (most recent) PMIDs first.
    """

    def __init__(self, lex, **kwargs):
        self.lex = lex
        self.pmid2citation = {}
        self.errors = []

        self.clinvar_results = None

        if kwargs.get('clinvar', True):
            self._load_clinvar()

        self.pubtator_results = None

        if kwargs.get('pubtator', True):
            self._load_pubtator()

        self.ncbi_results = None

        if kwargs.get('ncbi', True):
            self._load_ncbi()

        self.google_cse = None
        self.google_results = None

        if kwargs.get('google', True):
            self._load_google()

    @property
    def citations(self):
        """ Recompose pmid2citation table as a list of Citations, reverse-sorted by PMID.

        :return: list of Citation objects sorted by PMID (highest first)
        """
        citations = []
        for key in sorted(self.pmid2citation.keys(), reverse=True):
            citations.append(self.pmid2citation[key])
        return citations

    def _load_clinvar(self):
        # CLINVAR RESULTS
        log.info('[%s] Getting ClinVar results...', self.lex.hgvs_text)
        self.clinvar_results = ClinvarHgvs2Pmid(self.lex)

        for pmid in self.clinvar_results:
            try:
                cit = self.pmid2citation[pmid]
                cit.in_clinvar = True
            except KeyError:
                self.pmid2citation[pmid] = Citation(pmid, clinvar=True)

    def _load_pubtator(self):
        # PUBTATOR RESULTS
        log.info('[%s] Getting PubTator results...', self.lex.hgvs_text)
        self.pubtator_results = pubtator_results_for_lex(self.lex)

        for hgvs_text in self.pubtator_results:
            for row in self.pubtator_results[hgvs_text]:
                pmid = int(row['PMID'])
                try:
                    cit = self.pmid2citation[pmid]
                    cit.in_pubtator = True
                    cit.pubtator_mention = row['Mentions']
                    cit.pubtator_components = row['Components']
                except KeyError:
                    self.pmid2citation[pmid] = Citation(pmid, pubtator=True,
                                                    pubtator_mention=row['Mentions'],
                                                    pubtator_components=row['Components'])

    def _load_ncbi(self):
        # NCBI RESULTS
        log.info('[%s] Getting NCBI results...', self.lex.hgvs_text)
        try:
            self.ncbi_results = NCBIHgvs2Pmid(self.lex.hgvs_text)
        except NCBIRemoteError as error:
            self.errors.append('%r' % error)
            log.warn(error)

        if self.ncbi_results:
            for pmid in self.ncbi_results:
                try:
                    cit = self.pmid2citation[pmid]
                    cit.in_ncbi = True
                except KeyError:
                    self.pmid2citation[pmid] = Citation(pmid, ncbi=True)

    def _load_google(self):
        log.info('[%s] Getting Google results...', self.lex.hgvs_text)
        try:
            self.google_cse = GoogleCSEngine(self.lex)
            self.google_query = self.google_cse.build_query()
            #self.google_query_c = self.google_cse.query_c()
            #self.google_query_g = self.google_cse.query_g()
            #self.google_query_p = self.google_cse.query_p()
            #self.google_query_n = self.google_cse.query_n()
        except GoogleQueryMissingGeneName as error:
            self.errors.append('%r' % error)

        if self.google_cse:
            # TODO: allow configuration of seqtype array for send_query
            try:
                self.google_results = GoogleQuery(self.lex)
            except GoogleQueryRemoteError as error:
                self.google_results = []
                self.errors.append('%r' % error)
                log.warn(error)
                return

            for cseresult in self.google_results:
                if cseresult.pmid:
                    try:
                        cit = self.pmid2citation[cseresult.pmid]
                        cit.in_google = True
                        cit.google_result = cseresult
                    except KeyError:
                        self.pmid2citation[cseresult.pmid] = Citation(cseresult.pmid, google=True, google_result=cseresult)

    def to_dict(self):
        outd = self.__dict__
        return outd


class Citation(object):

    def __init__(self, pmid, **kwargs):

        self.pmid = pmid
        self.pma = fetch.article_by_pmid(pmid)

        self.in_pubtator = kwargs.get('pubtator', False)
        self.in_ncbi = kwargs.get('ncbi', False)
        self.in_clinvar = kwargs.get('clinvar', False)

        self.pubtator_mention = kwargs.get('pubtator_mention', None)
        self.pubtator_components = kwargs.get('pubtator_components', None)

        self.in_google = kwargs.get('google', False)
        self.google_result = kwargs.get('google_result', None)

        # placeholder for FindIt lookup of link to article PDF (if available)
        self._pdf_src = None

    @property
    def citation(self):
        return self.pma.citation

    @property
    def pdf_url(self):
        if self.pma.journal.lower().startswith('genereviews'):
            #TODO: make book_url a @property in metapub PubMedArticle
            return GENEREVIEWS_URL.format(bookid = self.pma.book_accession_id)

        if not self._pdf_src:
            self._pdf_src = FindIt(self.pmid, verify=False)
        return self._pdf_src.url

    @property
    def dxdoi_url(self):
        if self.pma.doi:
            return 'https://dx.doi.org/' + self.pma.doi
        return None

    @property
    def pubmed_url(self):
        return 'http://www.ncbi.nlm.nih.gov/pubmed/{pmid}'.format(pmid=self.pmid)

    @property
    def pubtator_url(self):
        url_tmpl = 'http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/curator_identifier.cgi?user=User63310122&pmid={pmid}&searchtype=PubMed_Search&query={pmid}&page=1&Species_display=1&Chemical_display=1&Gene_display=1&Disease_display=1&Mutation_display=1&tax='
        return url_tmpl.format(pmid=self.pmid)

    @property
    def clinvar_url(self):
        url_tmpl = 'http://www.ncbi.nlm.nih.gov/clinvar/?LinkName=pubmed_clinvar&uid={pmid}'
        return url_tmpl.format(pmid=self.pmid)

    @property
    def google_url(self):
        if self.google_result:
            return self.google_result.url

    @property
    def htmlSnippet(self):
        if self.google_result:
            return Markup(self.google_result.htmlSnippet)


class ClinVarInfo(object):

    def __init__(self, hgvs_text):
        self.variationID = hgvs_to_clinvar_variationID(hgvs_text)
        self.url = ''
        self.clinical_significance = ''

        if self.variationID:
            self.url = get_variation_url(self.variationID)
            #self.clinical_significance = get_variation_clinical_significance(self.variationID)


class GeneInfo(object):

    def __init__(self, gene_id=None, gene_name=None):
        if gene_id:
            self.gene_id = gene_id
            self.gene_name = GeneName(gene_id)
        elif gene_name:
            self.gene_name = gene_name
            self.gene_id = GeneID(gene_name)

    @property
    def ncbi_url(self):
        return 'http://www.ncbi.nlm.nih.gov/gene/{gene_id}'.format(gene_id=self.gene_id)

    @property
    def medgen_url(self):
        return 'http://www.ncbi.nlm.nih.gov/medgen?term={gene_name}%5BGene%5D'.format(gene_name=self.gene_name)

    @property
    def gtr_url(self):
        return 'http://www.ncbi.nlm.nih.gov/gtr/genes/{gene_id}'.format(gene_id=self.gene_id)

    @property
    def hgnc_url(self):
        return 'http://www.genenames.org/cgi-bin/search?search_type=all&search={}&submit=Submit'.format(self.gene_name)

    @property
    def gene_pubmeds_url(self):
        return 'http://www.ncbi.nlm.nih.gov/pubmed/?LinkName=gene_pubmed&from_uid={gene_id}'.format(gene_id=self.gene_id)

    @property
    def pubmed_clinical_query_url(self):
        return 'http://www.ncbi.nlm.nih.gov/pubmed/clinical?term={}[Gene]#clincat=Diagnosis,Narrow;medgen=Genetic'.format(self.gene_name)


def hgvs_to_clinvar_variationID(hgvs_text):
    var_ids = ClinvarVariationID(hgvs_text)
    if len(var_ids) > 0:
        return var_ids[0]
    else:
        return None


def get_variation_url(varID):
    return 'http://www.ncbi.nlm.nih.gov/clinvar/variation/{var_id}'.format(var_id=varID)


def get_clinvar_tables_containing_variant(hgvs_text):
    """ Return list of hgvs sample tables that contain this hgvs_text. """

    db = ClinVarDB()
    out = []
    tname_pattern = 'samples%'

    sql = "select TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA = DATABASE() and TABLE_NAME LIKE '{}'".format(tname_pattern)
    results = db.fetchall(sql)

    tables = []
    for row in results:
        tables.append(row['TABLE_NAME'])

    sql_tmpl = 'select * from {tname} where hgvs_text = "{hgvs_text}"'
    for tname in tables:
        if db.fetchall(sql_tmpl.format(tname=tname, hgvs_text=hgvs_text)):
            out.append(tname)

    return out
