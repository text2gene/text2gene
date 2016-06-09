#!ve/bin/python

from __future__ import print_function, unicode_literals

import IPython

from pubtatordb import PubtatorDB
from hgvs_lexicon import HgvsLVG, HgvsComponents, Variant
from hgvs_lexicon import config as hgvs_config
from text2gene.api import *

import hgvs.dataproviders.uta
import hgvs.parser
import hgvs.variantmapper

hgvs_parser = hgvs.parser.Parser()

#UTACONNECTION = 'postgresql://uta_admin:anonymous@192.168.1.3/uta_20150903'
#uta = hgvs.dataproviders.uta.connect(UTACONNECTION, pooling=True)
uta = hgvs.dataproviders.uta.connect()
mapper = hgvs.variantmapper.EasyVariantMapper(uta)


_EOL = '\r\n'

print(_EOL)
print(_EOL)

HEADER = """#################################################################
        text2gene / hgvs_lexicon / pubtatordb API shell

            UTA connection: {}:{}

            type 'whos' for api function list

#################################################################""".format(hgvs_config.UTA_HOST,
                                                                            hgvs_config.UTA_PORT)

hgvs_text_c1 = 'NM_001232.3:c.919G>C'
hgvs_text_c2 = 'NM_198578.3:c.6055G>A'

hgvs_text_delins = 'NM_000125.3:c.1339_1340delTGinsGC'
hgvs_text_intron = 'NM_033453.3:c.124+21A>C'

hgvs_text_g1 = 'NC_000001.10:g.100316615_100316616delAG'
hgvs_text_g2 = 'NC_000001.10:g.100345603G>T' 

#IPython.start_ipython()
IPython.embed(header=HEADER)


