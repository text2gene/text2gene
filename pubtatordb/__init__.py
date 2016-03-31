from __future__ import absolute_import

from MySQLdb import ProgrammingError

from .sqldata import SQLData
from .exceptions import PubtatorDBError

class PubtatorDB(SQLData):

    def _fetchall_or_raise_pubtatordberror(self, sql):
        try:
            return self.fetchall(sql)
        except ProgrammingError as error:
            # attempt to lookup an edittype that we don't currently handle (e.g. EXT, INV)
            raise PubtatorDBError('EditType %s cannot be handled. (%r)' % (comp.edittype, error))

    def search_FS(self, comp, gene_id, strict=False):
        if gene_id:
            sql = "select distinct M.* from gene2pubtator G, m2p_FS M where G.PMID = M.PMID and G.GeneID = {gene_id} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp, gene_id=gene_id)
        else:
            sql = "select distinct * from m2p_FS where SeqType = '{comp.seqtype}' and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp)
        return self.fetchall(sql)

    def search_m2p(self, comp, gene_id, strict=False):
        # sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos={comp.pos} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and SeqType='{comp.seqtype}'".format(comp=comp, gene_id=gene_id)
        if gene_id:
            sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp, gene_id=gene_id)
        else:
            sql = "select distinct * from m2p_{comp.edittype} where SeqType = '{comp.seqtype}' and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp)
        return self._fetchall_or_raise_pubtatordberror(sql)

    def search_proteins(self, comp, gene_id, strict=False):
        if gene_id:
            sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos = '{comp.pos}' and SeqType='p' and Ref = '{comp.ref}'".format(comp=comp, gene_id=gene_id)
        else:
            sql = "select distinct * from m2p_{comp.edittype} where SeqType = '{comp.seqtype}' and Pos = '{comp.pos}' and SeqType='p' and Ref = '{comp.ref}'".format(comp=comp)
        return self._fetchall_or_raise_pubtatordberror(sql)
