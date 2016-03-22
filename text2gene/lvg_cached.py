from __future__ import absolute_import, unicode_literals

import pickle
import logging

from hgvs_lexicon import HgvsLVG

from .exceptions import Text2GeneError
from .sqlcache import SQLCache
from .config import GRANULAR_CACHE

log = logging.getLogger('text2gene.lvg')

class HgvsLVGCached(SQLCache):

    VERSION = HgvsLVG.VERSION

    def __init__(self, granular=False, granular_table='lvg_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('hgvslvg')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

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
            result = self.retrieve(hgvs_text)
            if result:
                lexobj = pickle.loads(self.retrieve(hgvs_text))
                if force_granular:
                    self.store_granular(lexobj)
                return lexobj

        lexobj = HgvsLVG(hgvs_text)
        if lexobj:
            self.store(hgvs_text, pickle.dumps(lexobj))
            if self.granular:
                self.store_granular(lexobj)

            return lexobj
        else:
            raise Text2GeneError('HgvsLVG object could not be created from input hgvs_text %s' % hgvs_text)

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for HgvsLVGCached'.format(tname))

        self.execute("drop table if exists {}".format(tname))

        sql = """create table {} (
                  hgvs_text varchar(255) not null,
                  PMID int(11) default NULL,
                  version varchar(10) default NULL)""".format(tname)
        self.execute(sql)
        sql = 'call create_index("{}", "hgvs_text,PMID")'.format(tname)
        self.execute(sql)


# API Definitions

LVG = HgvsLVGCached(GRANULAR_CACHE).query
