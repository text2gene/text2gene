from pubtatordb.clinvardb import *
from text2gene.api import LVGEnriched

from metavariant import VariantComponents, Variant

db = ClinVarAminoDB()

sql_tmpl = "select * from clinvar.variant_components where Symbol='%s' and Ref='%s' and Pos='%s'"

clinvar_list = open('data/clinvar_random_samples.txt').readlines()

#def print_queries_for_lvg(lvg):
#    for variant in lvg.variants['p'].values():
#        comp = VariantComponents(variant)
#        print(comp)
#        print(sql_tmpl % (lvg.gene_name, comp.ref, comp.pos))


def do_queries_for_lvg(lvg):
    for variant in lvg.variants['p'].values():
        try:
            comp = VariantComponents(variant)
            print(comp)
            print(db.search(comp, lvg.gene_name))
        except Exception as error:
            print(error)
            print()

for line in clinvar_list:
    lvg = LVGEnriched(line.strip())
    do_queries_for_lvg(lvg)


