from __future__ import absolute_import, unicode_literals

import logging

from medgen.api import ClinvarVariationID, ClinVarDB
from medgen.api import GeneID, GeneName
from medgen.annotate.gene import GeneSynonyms

from metapub import PubMedFetcher, FindIt
from metapub.utils import rootdomain_of

from flask import Markup

from .googlequery import GoogleQuery, GoogleCSEngine
from .exceptions import NCBIRemoteError, GoogleQueryMissingGeneName, GoogleQueryRemoteError
from .ncbi import NCBIHgvs2Pmid
from .cached import ClinvarHgvs2Pmid
from .pmid_lookups import pubtator_results_for_lex

log = logging.getLogger('text2gene')

fetch = PubMedFetcher()

GENEREVIEWS_URL = 'https://www.ncbi.nlm.nih.gov/books/{bookid}/'



def mime_to_filetype(mime):
    """ Takes a string describing a MIME type and returns a more simplified "filetype"
    intended for human readability.

    In general, we're just stripping out the "application/" designation and then making
    sure the resultant string isn't totally long and ridiculous.  Looking at you,
    "vnd.openxmlformats-officedocument.spreadsheetml.sheet".

    :param mime: (str)
    :return: (str)
    """
    # ugh, Excel! http://stackoverflow.com/questions/974079/setting-mime-type-for-excel-document
    if not mime:
        return ''

    filetype = mime.replace('application/', '').lower()
    if filetype.startswith('vnd'):
        if 'excel' in filetype:
            filetype = 'xls'
        elif filetype == 'vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            filetype = 'xlsx'
    return filetype


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
        self.hgvs_text = lex.hgvs_text
        self.lex = lex
        self.pmid2citation = {}
        self.errors = []
        self.gene_synonyms = []
        self.unmapped_citations = []

        if self.lex.gene_name:
            self.gene_synonyms = GeneSynonyms(self.lex.gene_name)

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
                else:
                    #TODO: RawCitation object?
                    rawcit = cseresult.to_dict()
                    rawcit['domain'] = rootdomain_of(rawcit['url'])
                    rawcit['htmlSnippet'] = Markup(rawcit['htmlSnippet'])
                    rawcit['filetype'] = mime_to_filetype(rawcit['mime'])
                    self.unmapped_citations.append(rawcit)

    def to_dict(self):
        """ Returns dictionary representation of this CitationTable.

        Notes on the shape of some of the data in the resultant dictionary:

        'pmid2citation': pmid -> Citation.to_dict()
        'lex': LVGobject.to_dict()   (see metavariant.HgvsLVG)
        """
        outd = {'lex': self.lex.to_dict(),
                'errors': self.errors,
                'pubtator_results': self.pubtator_results,
                'google_results': self.google_results,
                'clinvar_results': self.clinvar_results,
                'ncbi_results': self.ncbi_results,
                'unmapped_citations': self.unmapped_citations,
                }
        outd['pmid2citation'] = {}
        for pmid, cit in (self.pmid2citation.items()):
            outd['pmid2citation'][pmid] = cit.to_dict()
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

    def to_dict(self, pdf_url=False):
        """ Returns dictionary representation of this Citation.

        Does not include PubMedArticle (self.pma) since this info can be quickly re-retrieved
        if needed later, and would result in a much bigger dictionary than needed here.

        Includes all other attributes and @property items by default except pdf_url
        (see keywords), since pdf_url may require a few extra seconds of processing time.

        Keywords:
            pdf_url (bool): allows inclusion of pdf_url in result [default: False].
        """
        outd = self.__dict__.copy()
        outd.pop('pma')
        outd.pop('_pdf_src')
        if pdf_url:
            outd['pdf_url'] = self.pdf_url
        outd['dxdoi_url'] = self.dxdoi_url
        outd['citation'] = self.pma.citation
        outd['pubmed_url'] = self.pubmed_url
        outd['pubtator_url'] = self.pubtator_url
        outd['clinvar_url'] = self.clinvar_url
        outd['google_url']  = self.google_url
        outd['htmlSnippet'] = self.htmlSnippet

        return outd

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
        return 'https://www.ncbi.nlm.nih.gov/pubmed/{pmid}'.format(pmid=self.pmid)

    @property
    def pubtator_url(self):
        url_tmpl = 'https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/curator_identifier.cgi?user=User63310122&pmid={pmid}&searchtype=PubMed_Search&query={pmid}&page=1&Species_display=1&Chemical_display=1&Gene_display=1&Disease_display=1&Mutation_display=1&tax='
        return url_tmpl.format(pmid=self.pmid)

    @property
    def clinvar_url(self):
        url_tmpl = 'https://www.ncbi.nlm.nih.gov/clinvar/?LinkName=pubmed_clinvar&uid={pmid}'
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
        return 'https://www.ncbi.nlm.nih.gov/gene/{gene_id}'.format(gene_id=self.gene_id)

    @property
    def medgen_url(self):
        return 'https://www.ncbi.nlm.nih.gov/medgen?term={gene_name}%5BGene%5D'.format(gene_name=self.gene_name)

    @property
    def gtr_url(self):
        return 'https://www.ncbi.nlm.nih.gov/gtr/genes/{gene_id}'.format(gene_id=self.gene_id)

    @property
    def hgnc_url(self):
        return 'http://www.genenames.org/cgi-bin/search?search_type=all&search={}&submit=Submit'.format(self.gene_name)

    @property
    def gene_pubmeds_url(self):
        return 'https://www.ncbi.nlm.nih.gov/pubmed/?LinkName=gene_pubmed&from_uid={gene_id}'.format(gene_id=self.gene_id)

    @property
    def pubmed_clinical_query_url(self):
        return 'https://www.ncbi.nlm.nih.gov/pubmed/clinical?term={}[Gene]#clincat=Diagnosis,Narrow;medgen=Genetic'.format(self.gene_name)


def hgvs_to_clinvar_variationID(hgvs_text):
    var_ids = ClinvarVariationID(hgvs_text)
    if len(var_ids) > 0:
        return var_ids[0]
    else:
        return None


def get_variation_url(varID):
    return 'https://www.ncbi.nlm.nih.gov/clinvar/variation/{var_id}'.format(var_id=varID)


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
