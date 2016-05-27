from __future__ import absolute_import, print_function

import time
import sys
import logging

from metapub import FindIt
from metapub.exceptions import MetaPubError

from pubtatordb import PubtatorDB

ch = logging.StreamHandler()
logging.getLogger('metapub').addHandler(ch)
logging.getLogger('metapub').setLevel(logging.INFO)


try:
    tablename = sys.argv[1]
except IndexError:
    print('Supply text2gene table name containing PMID column as argument to this script.')
    sys.exit()

entries = PubtatorDB().fetchall('select distinct(PMID) from text2gene.{}'.format(tablename))

print()
print('%i PMIDs found in text2gene.%s' % (len(entries), tablename))
print()

def dmesg(pmid, msg):
    print('[%s] <%i> %s' % (pmid, time.time(), msg))

for entry in entries:
    pmid = entry['PMID']
    dmesg(pmid, 'collecting')
    try:
        src = FindIt(pmid, verify=False)
    except MetaPubError as error:
        dmesg(pmid, '%r' % error)
        continue

    if src.url:
        dmesg(src.pmid, src.url)
    else:
        dmesg(src.pmid, src.reason)

