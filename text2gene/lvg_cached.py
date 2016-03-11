from __future__ import absolute_import, unicode_literals

import pickle

from hgvs_lexicon import HgvsLVG

from .exceptions import Text2GeneError
from .sqlcache import SQLCache


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


# API Definitions

LVG = HgvsLVGCached().query

