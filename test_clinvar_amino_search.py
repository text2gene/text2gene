from __future__ import print_function

from pubtatordb.clinvardb import *
from text2gene.api import LVGEnriched

from metavariant import VariantComponents, Variant

db = ClinVarAminoDB()

#clinvar_list = open('data/clinvar_random_samples.txt').readlines()

clinvar_list = []
identity_list = db.fetchall('select distinct(variant_name) from clinvar.variant_components group by variant_name')
for item in identity_list:
    clinvar_list.append(item['variant_name'].strip())

#def print_queries_for_lvg(lvg):
#    for variant in lvg.variants['p'].values():
#        comp = VariantComponents(variant)
#        print(comp)
#        print(sql_tmpl % (lvg.gene_name, comp.ref, comp.pos))


def print_line_in_clinvar_db(variant_name):
    sql = 'select * from clinvar.variant_components where variant_name="%s"' % variant_name
    rows = db.fetchall(sql)
    for row in rows:
        print(row)

def do_queries_for_lvg(lvg, strict=False):
    pmids = set()
    unusable = 0

    for variant in lvg.variants['p'].values():
        try:
            comp = VariantComponents(variant)
            result = db.search(comp, lvg.gene_name, strict=strict)
            if result:
                print('@@@ RESULTS for {gene} + {ref}|{pos}'.format(gene=lvg.gene_name, ref=comp.ref, pos=comp.pos))
                for item in result:
                    pmids.add(item['PMID'])
        except Exception as error:
            unusable += 1

    print('[%s] %i p-vars (%i unusable)' % (lvg.seqvar, len(lvg.hgvs_p), unusable))

    for pmid in pmids:
        print('\t* %s' % pmid)


    print()

    return len(pmids)

def get_results_for_lvg(lvg, strict):
    num_pmids = do_queries_for_lvg(lvg, strict)
    if str(lvg.seqvar).startswith('NM_'):
        if not num_pmids:
            print_line_in_clinvar_db(entry)
    return num_pmids


total_pmids_strict = 0
total_pmids_loose = 0

for entry in clinvar_list:
    try:
        lvg = LVGEnriched(entry)
        total_pmids_strict += get_results_for_lvg(lvg, strict=True)
        total_pmids_loose += get_results_for_lvg(lvg, strict=False)

    except:
        pass


print('Total in clinvar_list: %i' % len(clinvar_list))
print('Total PMIDs *strict*: %i' % total_pmids_strict)
print('Total PMIDs *loose*: %i' % total_pmids_loose)
print()
print('Done!')
print()



