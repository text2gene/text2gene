# Verified 8/11/2019

import os

from medgen.api import ClinVarDB

DATADIR = 'data/'

OUTFILE_TMPL = os.path.join(DATADIR, 'hgvs_%s_clinvar_samples.txt')

CLINVAR_TOP_GENES = [1956, 7157]

cdb = ClinVarDB()

MAX_SAMPLES = 50

"""select H.HGVS, H.VariationID, C.citation_id from clinvar_hgvs H, var_citations C where H.HGVS like 'NM_%' and H.VariationID = C.VariationID and C.citation_source = 'PubMed' limit 20;"""

def get_rows_from_clinvar_for_geneID(geneID):
    cherrypick_sql = 'select variant_name as HGVS from variant_summary where GeneID = {geneID} and variant_name like "NM_%"'
    return cdb.fetchall(cherrypick_sql.format(geneID=geneID))

def get_rows_from_clinvar(qual):
    sql = 'select H.HGVS , H.VariationID, C.citation_id from clinvar_hgvs H, var_citations C where {qual} and H.VariationID = C.VariationID and C.citation_source = "PubMed" order by rand() limit {limit}'
    return cdb.fetchall(sql.format(qual=qual, limit=MAX_SAMPLES))

def write_samples_to_file(prefix, rows):
    fname = OUTFILE_TMPL % prefix
    print('@@@ %s: Writing %i samples to %s\n' % (prefix, len(rows), fname))
    fh = open(OUTFILE_TMPL % prefix, 'w')
    for row in rows:
        fh.write(row['HGVS'] + '\n')
    fh.close()


samples = {'NM': { 'qual': 'H.HGVS like "NM_%"',
                   'rows': []}, 
           'NC': { 'qual': 'H.HGVS like "NC_%"',
                   'rows': []},
           'NP': {'qual': 'H.HGVS like "NP_%" and H.HGVS not like "%:p.?" and H.HGVS not like "%p.(=)"',
                  'rows': []},
          }

for prefix in list(samples.keys()):
    rows = get_rows_from_clinvar(samples[prefix]['qual'])
    if rows:
        write_samples_to_file(prefix, rows)
    else:
        print('@@@', prefix, 'returned ZERO results, which is weird...')

for geneID in CLINVAR_TOP_GENES:
    rows = get_rows_from_clinvar_for_geneID(geneID)
    write_samples_to_file('geneID-{}'.format(geneID), rows)

print()
print('@@@ DONE')
print()

