from __future__ import absolute_import, unicode_literals

from medgen.api import NCBIVariantReport
from hgvs_lexicon import Variant, HgvsLVG

from .sqlcache import SQLCache
from .config import GRANULAR_CACHE, CONFIG


def ncbi_report_to_variants(report):
    """ Parses Hgvs_* strings from NCBI report and creates a "variants" dictionary
    like the following (mimicking the HgvsLVG.variants attribute):

    {seqtype: { 'hgvs_string': SequenceVariant object }

    :param report: list of strings representing NCBI Variation Reporter output
    :return: dict as per structure above
    """
    variants = {'p': {}, 'c': {}, 'g': {}, 'n': {}}
    for seqtype in variants.keys():
        hgvs_text = report[0].get('Hgvs_%s' % seqtype, '').strip()
        if hgvs_text:
            # set up data structure just like HgvsLVG object, i.e.:
            # {seqtype: { 'hgvs_string': SequenceVariant object }
            seqvar = Variant(hgvs_text)
            variants[seqtype][str(seqvar)] = seqvar
    return variants

def ncbi_report_to_pubmeds(report):
    """ Parses PMIDs from NCBI report and returns as list of strings.

    :param report: list of strings representing NCBI Variation Reporter output
    :return: list of pubmeds found in report
    """
    return report[0]['PMIDs']


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
        self.variants = ncbi_report_to_variants(self.report)
        super(NCBIEnrichedLVG, self).__init__(hgvs_text,
                                              hgvs_c=self.hgvs_c,
                                              hgvs_g=self.hgvs_g,
                                              hgvs_p=self.hgvs_p,
                                              hgvs_n=self.hgvs_n)


class NCBIVariantPubmedsCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True, granular_table='ncbi_match'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert(self.granular_table, entry_pairs)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                return result

        report = NCBIReport(hgvs_text, skip_cache)
        result = ncbi_report_to_pubmeds(report)
        self.store(hgvs_text, result)
        if self.granular and result:
            self.store_granular(hgvs_text, result)
        return result


class NCBIVariantReportCachedQuery(SQLCache):

    VERSION = '0.0.1'

    def __init__(self, granular=True, granular_table='ncbi_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_report')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def _store_granular_hgvs_type(self, hgvs_text, hgvs_vars, seqtype):
        entry_pairs = [{'hgvs_text': hgvs_text,
                        'hgvs_%s' % seqtype: '%s' % item,
                        'version': self.VERSION} for item in hgvs_vars]

        self.batch_insert(self.granular_table, entry_pairs)

    def store_granular(self, hgvs_text, result):
        variants = ncbi_report_to_variants(result)
        for seqtype in variants.keys():
            if variants[seqtype]:
                # if there's a variant actually in there (sometimes there's not)...
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

NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(granular=GRANULAR_CACHE,
                                              granular_table=CONFIG.get('training', 'ncbi_match_table')).query
NCBIReport = NCBIVariantReportCachedQuery(granular=GRANULAR_CACHE,
                                          granular_table=CONFIG.get('training', 'ncbi_mappings_table')).query
