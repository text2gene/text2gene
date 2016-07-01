from __future__ import absolute_import, unicode_literals

import pickle
import logging

from metavariant import VariantLVG 

from .exceptions import Text2GeneError
from .sqlcache import SQLCache
from .config import GRANULAR_CACHE

log = logging.getLogger('text2gene.lvg')

class VariantLVGCached(SQLCache):

    VERSION = 0

    def __init__(self, granular=False, granular_table='lvg_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('hgvslvg')

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

        lexobj = VariantLVG(hgvs_text)
        if lexobj:
            self.store(hgvs_text, lexobj)
            if force_granular or self.granular:
                self.store_granular(lexobj)

            return lexobj
        else:
            raise Text2GeneError('VariantLVG object could not be created from input hgvs_text %s' % hgvs_text)

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
              version int(11) default NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)

        self.execute('call create_index("{}", "hgvs_text,hgvs_g")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_c")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_n")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_p")'.format(tname))


# API Definitions

LVG = VariantLVGCached(GRANULAR_CACHE).query
