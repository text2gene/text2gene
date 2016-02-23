from __future__ import absolute_import, print_function, unicode_literals

from medgen.api import GeneID

from pubtatordb import PubtatorDB
from hgvs_lexicon import HgvsLVG, HgvsComponents

pubtator_db = PubtatorDB()

def anythingelse(comp, gene_id):
    #sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos={comp.pos} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and SeqType='{comp.seqtype}'".format(comp=comp, gene_id=gene_id)
    sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp, gene_id=gene_id)
    return pubtator_db.fetchall(sql)

def pubtator_search_by_protein(comp, gene_id):
    sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos = '{comp.pos}' and SeqType='p' and Ref = '{comp.ref}'".format(comp=comp, gene_id=gene_id)
    print(sql)
    return pubtator_db.fetchall(sql)



if __name__=='__main__':
    import sys
    try:
        hgvs_text = sys.argv[1]
    except IndexError:
        print('Supply hgvs text as argument to this script.')
        sys.exit()

    print('Parsing and augmenting supplied HGVS string %s...' % hgvs_text)
    lex = HgvsLVG(hgvs_text)
    print()
    print(lex)

    gene_id = GeneID(lex.gene_name)
    print(lex.gene_name, gene_id)

    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype]:
            components = HgvsComponents(seqvar)
            print(seqtype, components)
            if seqtype == 'p':
                results = pubtator_search_by_protein(components, gene_id)
            else:
                results = anythingelse(components, gene_id)
            for res in results:
                pmids.add(res['PMID'])
            
    print(pmids)



"""
mysql> select distinct M.* from gene2pubtator G, m2p_SUB M where G.PMID = M.PMID and G.GeneID = 120892 and pos=6055 and Ref = 'G' and Alt = 'A' and SeqType='c'; 
+----------+----------------+-------------+---------+----------+------+------+------+
| PMID     | Components     | Mentions    | SeqType | EditType | Ref  | Pos  | Alt  |
+----------+----------------+-------------+---------+----------+------+------+------+
| 16758483 | c|SUB|G|6055|A | c.6055G>A   | c       | SUB      | G    | 6055 | A    |
| 17116211 | c|SUB|G|6055|A | c.6055G>A   | c       | SUB      | G    | 6055 | A    |
| 17222106 | c|SUB|G|6055|A | c.6055G > A | c       | SUB      | G    | 6055 | A    |
| 17235449 | c|SUB|G|6055|A | c.6055G>A   | c       | SUB      | G    | 6055 | A    |
| 18211709 | c|SUB|G|6055|A | c.6055G > A | c       | SUB      | G    | 6055 | A    |
| 26600626 | c|SUB|G|6055|A | c.6055 G>A  | c       | SUB      | G    | 6055 | A    |
+----------+----------------+-------------+---------+----------+------+------+------+
"""