from __future__ import absolute_import, unicode_literals

from medgen.api import NCBIVariantReport, NCBIVariantPubmeds
from hgvs_lexicon import Variant, HgvsLVG

from .sqlcache import SQLCache
from .config import GRANULAR_CACHE


def ncbi_report_to_variants(report):
    variants = {'p': {}, 'c': {}, 'g': {}, 'n': {}}
    for seqtype in variants.keys():
        hgvs_text = report[0].get('Hgvs_%s' % seqtype, '').strip()
        if hgvs_text:
            seqvar = Variant(hgvs_text)
            variants[seqtype] = seqvar
    return variants


class NCBIHgvsLVG(object):

    VERSION = '0.0.1'

    def __init__(self, hgvs_text, **kwargs):
        self.hgvs_text = hgvs_text
        self.report = NCBIReport(self.hgvs_text)
        self.variants = ncbi_report_to_variants(self.report)


class NCBIEnrichedLVG(HgvsLVG):

    VERSION = '0.0.1'

    def __init__(self, hgvs_text, **kwargs):
        self.variants = {'p': {}, 'c': {}, 'g': {}, 'n': {}}

        self.report = NCBIReport(str(hgvs_text))
        self._parse_report()

        super(NCBIEnrichedLVG, self).__init__(hgvs_text,
                                              hgvs_c=self.hgvs_c,
                                              hgvs_g=self.hgvs_g,
                                              hgvs_p=self.hgvs_p,
                                              hgvs_n=self.hgvs_n)

    def _parse_report(self):
        rep = self.report[0]
        for seqtype in self.variants.keys():
            hgvs_text = rep.get('Hgvs_%s' % seqtype, '').strip()
            if hgvs_text:
                seqvar = Variant(hgvs_text)
                self.variants[seqtype][str(seqvar)] = seqvar



class NCBIVariantPubmedsCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert('ncbi_match', entry_pairs)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        result = NCBIVariantPubmeds(hgvs_text)
        self.store(hgvs_text, result)
        if self.granular:
            self.store_granular(hgvs_text, result)
        return result


class NCBIVariantReportCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('ncbi_report')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def _store_granular_hgvs_type(self, hgvs_text, hgvs_vars, seqtype):
        entry_pairs = [{'hgvs_text': hgvs_text,
                        'hgvs_%s' % seqtype: '%s' % item,
                        'version': self.VERSION} for item in hgvs_vars]

        self.batch_insert('ncbi_mappings', entry_pairs)

    def store_granular(self, hgvs_text, result):
        #TODO: rename this and the others "store_grains"
        variants = ncbi_report_to_variants(result)
        for seqtype in variants.keys():
            self._store_granular_hgvs_type(hgvs_text, variants[seqtype], seqtype)

    def query(self, hgvs_text, skip_cache=False, force_granular=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                if force_granular:
                    self.store_granular(hgvs_text, result)
                return result

        result = NCBIVariantReport(hgvs_text)
        self.store(hgvs_text, result)
        if self.granular:
            self.store_granular(hgvs_text, result)
        return result


### API Functions

NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(GRANULAR_CACHE).query
NCBIReport = NCBIVariantReportCachedQuery(GRANULAR_CACHE).query
