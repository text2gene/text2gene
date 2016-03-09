from __future__ import absolute_import, unicode_literals

from medgen.api import NCBIVariantPubmeds

from .sqlcache import SQLCache
from .pmid_lookups import clinvar_hgvs_to_pmid, pubtator_hgvs_to_pmid

#### Cached Query classes: one "Hgvs2Pmid" for each service

class ClinvarCachedQuery(SQLCache):

    def __init__(self):
        super(self.__class__, self).__init__('clinvar_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def hgvs2pmid(self, hgvs_text, skip_cache=False):
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

    def hgvs2pmid(self, hgvs_text, skip_cache=False):
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

    def hgvs2pmid(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)

        if result:
            return result

        result = NCBIVariantPubmeds(hgvs_text)
        self.store(hgvs_text, result)
        return result


ClinvarHgvs2Pmid = ClinvarCachedQuery().hgvs2pmid
PubtatorHgvs2Pmid = PubtatorCachedQuery().hgvs2pmid
NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery().hgvs2pmid
