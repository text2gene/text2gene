from __future__ import absolute_import, unicode_literals

from medgen.api import NCBIVariantPubmeds, NCBIVariantReport

import logging

from .sqlcache import SQLCache
from .pmid_lookups import clinvar_hgvs_to_pmid, pubtator_hgvs_to_pmid
from .ncbi_lvg import ncbi_report_to_variants
from .config import GRANULAR_CACHE

log = logging.getLogger('text2gene.cached')

#### Cached Query classes: one "Hgvs2Pmid" for each service

# NOTE: remember to use sbin/init_cache.py ahead of first-time run, to create the necessary tables in MySQL.

class ClinvarCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('clinvar_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert('clinvar_match', entry_pairs)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = clinvar_hgvs_to_pmid(hgvs_text)
        self.store(hgvs_text, result)
        if self.granular:
            self.store_granular(hgvs_text, result)
        return result


class PubtatorCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('pubtator_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert('pubtator_match', entry_pairs)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = pubtator_hgvs_to_pmid(hgvs_text)
        self.store(hgvs_text, result)
        if self.granular:
            self.store_granular(hgvs_text, result)
        return result


class NCBIVariantPubmedsCachedQuery(SQLCache):

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid} for pmid in result]
        self.batch_insert('ncbi_match', entry_pairs)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = NCBIVariantPubmeds(hgvs_text)
        self.store(hgvs_text, result)
        return result


class NCBIVariantReportCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('ncbi_report')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        variants = ncbi_report_to_variants(result)

        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid} for pmid in result]
        self.batch_insert('ncbi_match', entry_pairs)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = NCBIVariantReport(hgvs_text)
        self.store(hgvs_text, result)
        if self.granular:
            self.store_granular(hgvs_text, result)
        return result


### API Definitions

ClinvarHgvs2Pmid = ClinvarCachedQuery(GRANULAR_CACHE).query
PubtatorHgvs2Pmid = PubtatorCachedQuery(GRANULAR_CACHE).query
NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(GRANULAR_CACHE).query
NCBIReport = NCBIVariantReportCachedQuery(GRANULAR_CACHE).query

