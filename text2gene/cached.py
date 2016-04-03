from __future__ import absolute_import, unicode_literals

import logging

from .sqlcache import SQLCache
from .pmid_lookups import clinvar_lex_to_pmid, pubtator_lex_to_pmid
from .config import GRANULAR_CACHE

log = logging.getLogger('text2gene.cached')

#### Cached Query classes: one "Hgvs2Pmid" for each service

# NOTE: remember to use sbin/init_cache.py ahead of first-time run, to create the necessary tables in MySQL.

class ClinvarCachedQuery(SQLCache):

    VERSION = 0

    def __init__(self, granular=False, granular_table='clinvar_match'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('clinvar_hgvs2pmid')

    def get_cache_key(self, lex):
        """ Returns a cache_key in the following shape:

        "<hgvs_text>@<lvg_mode>"

        :param lex: any variant LVG object (HgvsLVG, NCBIEnrichedLVG, etc)
        :return: key generated from relevant details in lex
        """
        tmpl = '{hgvs_text}@{lvg_mode}'
        return tmpl.format(hgvs_text=lex.hgvs_text, lvg_mode=lex.LVG_MODE)

    def store_granular(self, lex, result):
        entry_pairs = [{'hgvs_text': lex.hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert(self.granular_table, entry_pairs)

    def query(self, lex, skip_cache=False, force_granular=False):
        """
        :param lex: any lexical variant object (HgvsLVG, NCBIEnrichedLVG, NCBIHgvsLVG)
        :param skip_cache: whether to force reloading the data by skipping the cache
        :return: list of PMIDs if found (result of Clinvar query)
        """
        if not skip_cache:
            result = self.retrieve(lex, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(lex, result)
                return result

        result = clinvar_lex_to_pmid(lex)
        self.store(lex, result)
        if (force_granular or self.granular) and result:
            self.store_granular(lex, result)
        return result

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for ClinvarCachedQuery'.format(tname))

        self.execute("drop table if exists {}".format(tname))

        sql = """create table {} (
                  hgvs_text varchar(255) not null,
                  PMID int(11) default NULL,
                  version int(11) default 0)
                  ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)
        sql = 'call create_index("{}", "hgvs_text,PMID")'.format(tname)
        self.execute(sql)


class PubtatorCachedQuery(SQLCache):

    VERSION = 0

    def __init__(self, granular=False, granular_table='pubtator_match'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('pubtator_hgvs2pmid')

    def get_cache_key(self, lex):
        """ Returns a cache_key in the following shape:

        "<hgvs_text>@<lvg_mode>"

        :param lex: any variant LVG object (HgvsLVG, NCBIEnrichedLVG, etc)
        :return: key generated from relevant details in lex
        """
        tmpl = '{hgvs_text}@{lvg_mode}'
        return tmpl.format(hgvs_text=lex.hgvs_text, lvg_mode=lex.LVG_MODE)

    def store_granular(self, lex, result):
        entry_pairs = [{'hgvs_text': lex.hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert(self.granular_table, entry_pairs)

    def query(self, lex, skip_cache=False, force_granular=False):
        """
        :param lex: any lexical variant object (HgvsLVG, NCBIEnrichedLVG, NCBIHgvsLVG)
        :param skip_cache: whether to force reloading the data by skipping the cache
        :return: list of PMIDs if found (result of Clinvar query)
        """
        if not skip_cache:
            result = self.retrieve(lex, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(lex, result)
                return result

        result = pubtator_lex_to_pmid(lex)
        self.store(lex, result)
        if (force_granular or self.granular) and result:
            self.store_granular(lex, result)
        return result

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for PubtatorCachedQuery'.format(tname))

        self.execute("drop table if exists {}".format(tname))
        # ComponentString varchar(255) default NULL,  # TODO add in later. too complicated right now.

        sql = """create table {} (
                  hgvs_text varchar(255) not null,
                  PMID int(11) default NULL,
                  version int(11) default NULL)
                  ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)
        sql = 'call create_index("{}", "hgvs_text,PMID")'.format(tname)
        self.execute(sql)


### API Definitions

ClinvarHgvs2Pmid = ClinvarCachedQuery(granular=GRANULAR_CACHE).query
PubtatorHgvs2Pmid = PubtatorCachedQuery(granular=GRANULAR_CACHE).query
