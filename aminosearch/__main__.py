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
    if not comp:
        print('[%s] INVALID Amino Change' % achg)
        return

    print('[%s] Posedit: %s' % (achg, comp.posedit))
    print('[%s] Slang: %r' % (achg, comp.posedit_slang))

    gene_id = GeneID(gene)
    print('[%s] Gene: %s (ID: %i)' % (achg, gene, gene_id))

    #results = cvdb.search(comp, gene_id, strict=False)
    #print('[%s] Clinvar LOOSE matches: %r' % (achg, results))

    results = cvdb.search(comp, gene_id, strict=True)
    print('[%s] Clinvar STRICT matches: %i' % (achg, len(results)))
    
    for res in results:
        print('[%s]' % achg, res['PMID'], res['HGVS'], res['VariationID'], res['GeneSymbol'], res['Ref'], res['Pos'], res['Alt'])

    results = pubdb.search_proteins(comp, gene_id)
    print('[%s] PubtatorDB matches: %i' % (achg, len(results)))
    for res in results:
        print(res)

def main():
    import sys
    gene = sys.argv[1]
    aminochange = sys.argv[2]
    search_aminoDBs(gene, aminochange)


if __name__=='__main__':
    main()

