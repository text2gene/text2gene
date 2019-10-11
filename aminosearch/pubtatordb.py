from __future__ import absolute_import, unicode_literals

from MySQLdb import ProgrammingError

#from medgen.db.dataset import SQLData 
from .sqldata import SQLData
from .exceptions import PubtatorDBError

class PubtatorDB(SQLData):

    def _fetchall_or_raise_pubtatordberror(self, sql, comp, *args):
        try:
            return self.fetchall(sql, *args)
        except ProgrammingError as error:
            # attempt to lookup an edittype that we don't currently handle (e.g. EXT, INV)
            raise PubtatorDBError('EditType %s currently not handled. (%r)' % (comp.edittype, error))

    def search_FS(self, comp, gene_id, strict=False):
        if gene_id:
            sql = 'select distinct M.* from gene2pubtator G, m2p_FS M where G.PMID = M.PMID and G.GeneID=%s and Ref="%s" and Alt="%s" and Pos=%s'
            args = (gene_id, comp.ref, comp.alt, comp.pos)
        else:
            sql = 'select distinct * from m2p_FS where SeqType="%s", and Ref="%s" and Alt="%s" and Pos=%s'
            args = (comp.seqtype, comp.ref, comp.alt, comp.pos)

        return self.fetchall(sql, *args)

    def search_m2p(self, comp, gene_id, strict=False):
        # sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos={comp.pos} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and SeqType='{comp.seqtype}'".format(comp=comp, gene_id=gene_id)
        if gene_id:
            sql = 'select distinct M.* from gene2pubtator G, m2p_'+comp.edittype+' M where G.PMID = M.PMID and G.GeneID=%s and Ref="%s" and Alt="%s" and Pos=%s'
            args = (gene_id, comp.ref, comp.alt, comp.pos)
        else:
            sql = 'select distinct * from m2p_'+comp.edittype+' where SeqType="%s" and Ref="%s" and Alt="%s" and Pos=%s'
            args = (comp.seqtype, comp.ref, comp.alt, comp.pos)

        return self._fetchall_or_raise_pubtatordberror(sql, comp, *args)

    def search_proteins(self, comp, gene_id, strict=False):
        if not comp.edittype:
            tablename = 'm2p_general'
        else:
            tablename = 'm2p_%s' % comp.edittype

        if gene_id:
            sql = 'select distinct M.* from gene2pubtator G, '+tablename+' M where G.PMID = M.PMID and G.GeneID=%s and Pos="%s" and SeqType="p" and Ref="%s"'
            args = (gene_id, comp.pos, comp.ref)
        else:
            sql = 'select distinct * from '+tablename+' where SeqType="%s" and Pos=%s and SeqType="p" and Ref="%s"'
            args = (comp.seqtype, comp.pos, comp.ref)

        if strict:
            sql += ' and Alt = "%s"'
            args = (args, comp.alt)

        return self._fetchall_or_raise_pubtatordberror(sql, comp, *args)

