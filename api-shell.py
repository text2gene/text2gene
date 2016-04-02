#!/usr/bin/env python

import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    try:
        import IPython
    except ImportError:
        import os
        os.popen('pip install ipython')
        import IPython

from pubtatordb import PubtatorDB
from hgvs_lexicon import HgvsLVG, HgvsComponents, Variant
from text2gene import *

import hgvs.dataproviders.uta
import hgvs.parser
import hgvs.variantmapper

hgvs_parser = hgvs.parser.Parser()

#UTACONNECTION = 'postgresql://uta_admin:anonymous@192.168.1.3/uta_20150903'
#uta = hgvs.dataproviders.uta.connect(UTACONNECTION, pooling=True)
uta = hgvs.dataproviders.uta.connect()
mapper = hgvs.variantmapper.EasyVariantMapper(uta)


_EOL = '\r\n'

print _EOL
print _EOL

print('#################################################################')
print(' text2gene ')
print()
print('        type whos for api function list')
print()
print('              In [1]: whos ')
print()
print('#################################################################')

hgvs_text_c1 = 'NM_001232.3:c.919G>C'
hgvs_text_c2 = 'NM_198578.3:c.6055G>A'

hgvs_text_g1 = 'NC_000001.10:g.100316615_100316616delAG'
hgvs_text_g2 = 'NC_000001.10:g.100345603G>T' 

IPython.embed()

