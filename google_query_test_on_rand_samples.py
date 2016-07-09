from __future__ import absolute_import, print_function, unicode_literals

import sys
import logging

from text2gene.googlequery import GoogleQuery, GoogleCSEngine, googlecse2pmid
from text2gene.api import LVGEnriched
from text2gene.exceptions import Text2GeneError

from medgen.api import ClinVarDB

from metavariant.exceptions import *

RESULTS_TABLE = 'text2gene.googlequery_rand_test'

db = ClinVarDB()

log = logging.getLogger('text2gene.*')
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

logging.getLogger('hgvs_lexicon').addHandler(ch)


def dmesg(hgvs_text, msg):
    print('[%s] %s' % (hgvs_text, msg))

def print_result(hgvs_text, cseres, idx):
    if cseres.pmid:
        dmesg(hgvs_text, '%i) Resolved: %s' % (idx, cseres.pmid))
    else:
        dmesg(hgvs_text, '%i) Unresolved:' % idx)
    dmesg(hgvs_text, '    url: %s' % cseres.url)
    dmesg(hgvs_text, '    doi: %s' % cseres.doi)


rows = ClinVarDB().fetchall('select * from rand_samples')
print('Found %i hgvs_text samples in rand_samples' % len(rows))
print()
print('Creating google query results table in text2gene DB...')
print()

db.execute("drop table if exists %s" % RESULTS_TABLE)
db.execute("create table %s like clinvar.samples" % RESULTS_TABLE)
db.execute("alter table %s add column qstring text default NULL" % RESULTS_TABLE)
db.execute("alter table %s add column seqtype varchar(10) default 'all'" % RESULTS_TABLE)
db.execute("alter table %s add column num_pmids int(11) default 0" % RESULTS_TABLE)
db.execute("alter table %s add column num_results int(11) default 0" % RESULTS_TABLE)
db.execute("alter table %s add column pmids varchar(255) default 0" % RESULTS_TABLE)


def record_result(row, seqtype='all', qstring='', pmids=[], num_results=0, error=None):
    row['num_pmids'] = len(pmids)
    row['pmids'] = pmids
    row['seqtype'] = seqtype
    row['num_results'] = num_results
    row['qstring'] = qstring

    #print('STORING RESULT: %r' % row)
    db.insert(RESULTS_TABLE, row)


for row in rows:
    hgvs_text = row['hgvs_text'].strip()

    try:
        lex = LVGEnriched(hgvs_text)
    except CriticalHgvsError as error:
        dmesg(hgvs_text, '%r' % error)
        continue

    # do the amalgamated query. track results.
    try:
        gcse = GoogleCSEngine(lex)
    except Text2GeneError as error:
        print('@@@ Error setting up GoogleCSEngine object for %s' % hgvs_text)
        dmesg(hgvs_text, '%r' % error)
        #record_error(row, error)
        print()
        continue

    # try each of the 5 styles of query. track results.
    pmids_by_seqtype = {'all': [], 'c': [], 'g': [], 'n': [], 'p': []}
    for seqtype in pmids_by_seqtype.keys():
        try:
            if seqtype == 'all':
                qstring = gcse.build_query()
                cse_results = GoogleQuery(lex)
            else:
                qstring = gcse.build_query(seqtypes=[seqtype])
                cse_results = GoogleQuery(lex, seqtypes=[seqtype])
        except Text2GeneError as error:
            dmesg(hgvs_text, '%r' % error)
            record_result(row, seqtype, error=error)
            continue

        if cse_results:
            pmids_by_seqtype[seqtype] = googlecse2pmid(cse_results)

        dmesg(hgvs_text, 'SEQTYPE: %s' % seqtype)
        dmesg(hgvs_text, ' == Google query: %s' % qstring)
        dmesg(hgvs_text, ' == PMIDs: %i' % len(pmids_by_seqtype[seqtype]))
        dmesg(hgvs_text, ' == Google CSE Results: %i' % len(cse_results))

        resolved = []
        idx = 0
        for cseres in cse_results:
            if cseres.pmid:
                resolved.append(cseres)
            print_result(hgvs_text, cseres, idx)
            idx += 1

        dmesg(hgvs_text, ' == Total Resolved: %i / %i' % (len(resolved), len(cse_results)))
        print()
        record_result(row, pmids=pmids_by_seqtype[seqtype], qstring=qstring, num_results=len(cse_results), seqtype=seqtype)

    print()



