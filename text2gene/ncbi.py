""" Provides NCBIHgvs2Pmid, NCBIReport, and LVGEnriched cached query engines.

Under the hood, the algorithmic work is being handled by metavariant."""

#TODO: replace pickle with JSON
import pickle
import logging

import requests
from metavariant import NCBIEnrichedLVG

from .sqlcache import SQLCache
from .config import GRANULAR_CACHE, SEQVAR_MAX_LEN
from .exceptions import Text2GeneError

log = logging.getLogger('text2gene.ncbi')


class NCBIEnrichedLVGCachedQuery(SQLCache):

    VERSION = 1

    def __init__(self, granular=False, granular_table='ncbi_enriched_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_enriched_lvg')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def get_cache_value(self, obj):
        """ Returns pickled object representation of supplied object. """
        return pickle.dumps(obj)

    def retrieve(self, hgvs_text, version=0):
        """ If cache contains a value for hgvs_text, retrieve it. Otherwise, return None.

        (Overrides default retrieve)

        If requested version number is GREATER THAN OR EQUAL TO version number of existing data, older version will be
        destroyed so that newer version can be created in its place.

        Thus, supplying version=0 allows returns from cache from *any* version of data that has ever been stored.

        :param hgvs_text: (str)
        :param version: (int) only return results from cache with greater than or equal version number [default: 0]
        :return: LVG object or None
        """
        row = self.get_row(hgvs_text)
        if row:
            if row['version'] >= version:
                return pickle.loads(row['cache_value'].decode('string_escape'))
            else:
                log.debug('Expiring obsolete entry at cache_key location %s.', self.get_cache_key(hgvs_text))
                self.delete(hgvs_text)
        return None

    def _store_granular_hgvs_type(self, lex, hgvs_seqtype_name):
        hgvs_vars = getattr(lex, hgvs_seqtype_name)
        if hgvs_vars:
            entry_pairs = [{'hgvs_text': lex.hgvs_text,
                            hgvs_seqtype_name: item,
                            'version': self.VERSION} for item in hgvs_vars]

            self.batch_insert(self.granular_table, entry_pairs)

    def store_granular(self, lex):
        for hgvs_type in ['c', 'g', 'n', 'p']:
            self._store_granular_hgvs_type(lex, 'hgvs_'+hgvs_type)

    def query(self, hgvs_text, skip_cache=False, force_granular=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(result)
                return result

        lexobj = NCBIEnrichedLVG(hgvs_text, seqvar_max_len=SEQVAR_MAX_LEN)
        if lexobj:
            self.store(hgvs_text, lexobj)
            if force_granular or self.granular:
                self.store_granular(lexobj)
            return lexobj
        else:
            raise Text2GeneError('NCBIEnrichedLVG object could not be created from input hgvs_text %s' % hgvs_text)

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for NCBIEnrichedLVGCachedQuery'.format(tname))

        self.execute("drop table if exists {};".format(tname))

        sql = """create table {} (
              hgvs_text varchar(255) not null,
              hgvs_g varchar(255) default NULL,
              hgvs_c varchar(255) default NULL,
              hgvs_n varchar(255) default NULL,
              hgvs_p varchar(255) default NULL,
              version varchar(10) default NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)

        self.execute('call create_index("{}", "hgvs_text,hgvs_g")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_c")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_n")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_p")'.format(tname))


class NCBIVariantPubmedsCachedQuery(SQLCache):

    VERSION = 0

    def __init__(self, granular=False, granular_table='ncbi_match'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert(self.granular_table, entry_pairs)

    def query(self, hgvs_text, skip_cache=False, force_granular=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(hgvs_text, result)
                return result

        report = NCBIReport(hgvs_text, skip_cache)
        result = ncbi_report_to_pubmeds(report)
        self.store(hgvs_text, result)
        if (force_granular or self.granular) and result:
            self.store_granular(hgvs_text, result)
        return result

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for NCBIVariantPubmedsCachedQuery'.format(tname))

        self.execute("drop table if exists {}".format(tname))

        sql = """create table {} (
                  hgvs_text varchar(255) not null,
                  PMID int(11) default NULL,
                  version varchar(10) default NULL)
                  ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)
        sql = 'call create_index("{}", "hgvs_text,PMID")'.format(tname)
        self.execute(sql)


class NCBIVariantReportCachedQuery(SQLCache):

    VERSION = 0

    MAXIMUM_REPORT_ENTRIES = 6

    def __init__(self, granular=False, granular_table='ncbi_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_report')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def _limit_report(self, report):
        """ Limit length of report to MAXIMUM_REPORT_ENTRIES records.

        Usually doesn't matter (most reports have at most 2 entries), but there are some
        freaks with 60+ (!).

        See tests/demo_NCBI_long_report_examples.py

        We find that the last usual location of unique variant info is at report index 5.
        If we try to keep these huge reports at full size, we can't cache them in SQL tables.

        :param: report (list of dictionaries)
        :return: report (list of dictionaries) possibly reduced in length.
        """
        if len(report) > self.MAXIMUM_REPORT_ENTRIES:
            return report[:self.MAXIMUM_REPORT_ENTRIES]
        else:
            return report

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
            result = self.retrieve(hgvs_text, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(hgvs_text, result)
                return result

        report = self._limit_report(get_ncbi_variant_report(hgvs_text))
        self.store(hgvs_text, report)
        if force_granular or self.granular:
            self.store_granular(hgvs_text, report)
        return report

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for NCBIVariantReportCachedQuery'.format(tname))

        self.execute("drop table if exists {};".format(tname))

        sql = """create table {} (
              hgvs_text varchar(255) not null,
              hgvs_g varchar(255) default NULL,
              hgvs_c varchar(255) default NULL,
              hgvs_n varchar(255) default NULL,
              hgvs_p varchar(255) default NULL,
              version varchar(10) default NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)

        self.execute('call create_index("{}", "hgvs_text,hgvs_g")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_c")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_n")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_p")'.format(tname))


# == API Functions == #

NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(granular=GRANULAR_CACHE).query
NCBIReport = NCBIVariantReportCachedQuery(granular=GRANULAR_CACHE).query
LVGEnriched = NCBIEnrichedLVGCachedQuery(granular=GRANULAR_CACHE).query
