from __future__ import absolute_import, unicode_literals

import pickle

from medgen.api import NCBIVariantPubmeds, NCBIVariantReport

from hgvs_lexicon import HgvsLVG

from .exceptions import Text2GeneError
from .sqlcache import SQLCache
from .pmid_lookups import clinvar_hgvs_to_pmid, pubtator_hgvs_to_pmid

#### Cached Query classes: one "Hgvs2Pmid" for each service

# NOTE: remember to use sbin/init_cache.py ahead of first-time run, to create the necessary tables in MySQL.


class HgvsLVGCached(SQLCache):
    def __init__(self):
        super(self.__class__, self).__init__('hgvslvg')

    def get_cache_key(querydict, hgvs_text):
        return str(hgvs_text)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                lexobj = pickle.loads(self.retrieve(hgvs_text))
                return lexobj

        lexobj = HgvsLVG(hgvs_text)
        if lexobj:
            self.store(hgvs_text, pickle.dumps(lexobj))
            return lexobj
        else:
            raise Text2GeneError('HgvsLVG object could not be created from input hgvs_text %s' % hgvs_text)


class ClinvarCachedQuery(SQLCache):

    def __init__(self):
        super(self.__class__, self).__init__('clinvar_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = clinvar_hgvs_to_pmid(hgvs_text)
        self.store(hgvs_text, result)
        return result


class PubtatorCachedQuery(SQLCache):

    def __init__(self):
        super(self.__class__, self).__init__('pubtator_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = pubtator_hgvs_to_pmid(hgvs_text)
        self.store(hgvs_text, result)
        return result


class NCBIVariantPubmedsCachedQuery(SQLCache):

    def __init__(self):
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = NCBIVariantPubmeds(hgvs_text)
        self.store(hgvs_text, result)
        return result


class NCBIVariantReportCachedQuery(SQLCache):

    def __init__(self):
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = NCBIVariantReport(hgvs_text)
        self.store(hgvs_text, result)
        return result


### API Definitions

LVG = HgvsLVGCached().query
ClinvarHgvs2Pmid = ClinvarCachedQuery().query
PubtatorHgvs2Pmid = PubtatorCachedQuery().query
NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery().query
NCBIReport = NCBIVariantReportCachedQuery().query

