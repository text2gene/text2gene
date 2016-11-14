from __future__ import absolute_import, print_function

from metavariant import VariantComponents
from medgen.api import GeneID

from .clinvardb import ClinVarAminoDB
from .pubtatordb import PubtatorDB

cvdb = ClinVarAminoDB()
pubdb = PubtatorDB()

def search_aminoDBs(gene, achg):
    print('[%s]' % achg)
    comp = VariantComponents(aminochange=achg)

    gene_id = GeneID(gene)

    results = cvdb.search(comp, gene_id, strict=False)
    print('[%s] Clinvar LOOSE matches: %r' % (achg, results))

    results = cvdb.search(comp, gene_id, strict=True)
    print('[%s] Clinvar STRICT matches: %r' % (achg, results))

    results = pubdb.search_proteins(comp, gene_id)
    print('[%s] PubtatorDB matches: %r' % (achg, results)) 

def main():
    import sys
    gene = sys.argv[1]
    aminochange = sys.argv[2]
    search_aminoDBs(gene, aminochange)


if __name__=='__main__':
    main()

