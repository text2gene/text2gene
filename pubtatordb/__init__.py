from __future__ import absolute_import

from .sqldata import SQLData


class PubtatorDB(SQLData):

    def search_FS(self, comp, gene_id, strict=False):
        sql = "select distinct M.* from gene2pubtator G, m2p_FS M where G.PMID = M.PMID and G.GeneID = {gene_id} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp, gene_id=gene_id)
        return self.fetchall(sql)

    def search_m2p(self, comp, gene_id, ):
        #sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos={comp.pos} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and SeqType='{comp.seqtype}'".format(comp=comp, gene_id=gene_id)
        sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp, gene_id=gene_id)
        return self.fetchall(sql)

    def search_proteins(self, comp, gene_id):
        sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos = '{comp.pos}' and SeqType='p' and Ref = '{comp.ref}'".format(comp=comp, gene_id=gene_id)
        return self.fetchall(sql)

