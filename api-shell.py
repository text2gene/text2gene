#!/usr/bin/env python

from medgen.api import *
from pubtatordb import PubtatorDB

_EOL = '\r\n'

print _EOL
print _EOL

print '#################################################################'
print ' text2gene '
print
print '        type whos for api function list'

print  '              In [1]: whos '
print
print '#################################################################'

hgvs_text  = 'NM_001232.3:c.919G>C'
hgvs_text2 = 'NM_198578.3:c.6055G>A'

import IPython
IPython.embed()
