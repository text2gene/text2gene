from __future__ import print_function

import os

from medgen.api import ClinVarDB

DATADIR = 'data/'

OUTFILE_TMPL = os.path.join(DATADIR, '%s_hgvs_clinvar_samples.txt')

cdb = ClinVarDB()

MAX_SAMPLES = 50

def get_rows_from_clinvar(qual):
    sql = 'select distinct(hgvs_text) from clinvar_hgvs where {qual} limit {limit}'.format(qual=qual, limit=MAX_SAMPLES)
    return cdb.fetchall(sql)


def write_samples_to_file(prefix, rows):
    fh = open(OUTFILE_TMPL % prefix, 'w')
    for row in rows:
        fh.write(row['hgvs_text'] + '\n')
    fh.close()


samples = {'NM': { 'qual': 'hgvs_text like "NM_%"',
                   'rows': []}, 
           'NC': { 'qual': 'hgvs_text like "NC_%"',
                   'rows': []},
           'NP': {'qual': 'hgvs_text like "NP_%" and hgvs_text not like "%:p.?" and hgvs_text not like "%p.(=)"',
                  'rows': []},
          }

for prefix in list(samples.keys()):
    rows = get_rows_from_clinvar(samples[prefix]['qual'])
    if rows:
        print('@@@', prefix, 'returned %i samples' % len(rows))
        write_samples_to_file(prefix, rows)
    else:
        print('@@@', prefix, 'returned ZERO results, which is weird...') 

print()
print('@@@ DONE')
print()

