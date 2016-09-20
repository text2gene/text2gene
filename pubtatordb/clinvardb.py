from __future__ import absolute_import, unicode_literals

from MySQLdb import ProgrammingError

from .sqldata import SQLData

class ClinVarAminoDB(SQLData):

    def _fetchall_or_raise_exception(self, sql, comp, *args):
        try:
            return self.fetchall(sql, *args)
        except ProgrammingError as error:
            # attempt to lookup an edittype that we don't currently handle (e.g. EXT, INV)
            raise Exception('EditType %s currently not handled. (%r)' % (comp.edittype, error))

    def search_clinvar_strict(self, comp, gene_name):
        if gene_name:
            sql = 'select * from clinvar.variant_components where GeneID=%s and Ref=%s and Alt=%s and Pos=%s'
            args = (gene_name, comp.ref, comp.alt, comp.pos)
        else:
            sql = 'select * from clinvar.variant_components where Ref=%s and Alt=%s and Pos=%s'
            args = (comp.ref, comp.alt, comp.pos)
        return self.fetchall(sql, *args)

    def search_clinvar_loose(self, comp, gene_name):
        if gene_name:
            sql = 'select * from clinvar.variant_components where Symbol=%s and Ref=%s and Pos=%s'
            args = (gene_name, comp.ref, comp.pos)
        else:
            sql = 'select * from clinvar.variant_components where Ref=%s and Pos=%s'
            args = (comp.ref, comp.pos)
        return self.fetchall(sql, *args)

    def search(self, comp, gene_name, strict=False):
        if strict:
            return self.search_clinvar_strict(comp, gene_name)
        else:
            return self.search_clinvar_loose(comp, gene_name)

        return self._fetchall_or_raise_exception(sql, comp, *args)

