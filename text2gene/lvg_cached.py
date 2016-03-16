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

    def __init__(self, granular=True):
        self.granular = granular
        super(self.__class__, self).__init__('hgvslvg')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def _store_granular_hgvs_type(self, lex, hgvs_seqtype_name):
        hgvs_vars = getattr(lex, hgvs_seqtype_name)
        entry_pairs = [{'hgvs_text': lex.hgvs_text,
                        hgvs_seqtype_name: item,
                        'version': self.VERSION} for item in hgvs_vars]

        self.batch_insert('lvg_mappings', entry_pairs)

    def store_granular(self, lex):
        for hgvs_type in ['c', 'g', 'n', 'p']:
            self._store_granular_hgvs_type(lex, 'hgvs_'+hgvs_type)

    def query(self, hgvs_text, skip_cache=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text)
            if result:
                lexobj = pickle.loads(self.retrieve(hgvs_text))
                return lexobj

        lexobj = HgvsLVG(hgvs_text)
        if lexobj:
            self.store(hgvs_text, pickle.dumps(lexobj))
            if self.granular:
                self.store_granular(lexobj)

            return lexobj
        else:
            raise Text2GeneError('HgvsLVG object could not be created from input hgvs_text %s' % hgvs_text)


# API Definitions

LVG = HgvsLVGCached(GRANULAR_CACHE).query
