from __future__ import absolute_import, print_function, unicode_literals

from medgen.api import GeneID, ClinvarPubmeds

from pubtatordb import PubtatorDB
from hgvs_lexicon import HgvsLVG, HgvsComponents, RejectedSeqVar

from .sqlcache import SQLCache
from .config import log

pubtator_db = PubtatorDB()


def _guard_lex(hgvs_lex_or_text):
    if type(hgvs_lex_or_text) == str:
        return HgvsLVG(hgvs_lex_or_text)
    else:
        return hgvs_lex_or_text


def clinvar_hgvs_to_pmid(hgvs_lex_or_text):
    lex = _guard_lex(hgvs_lex_or_text)
    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype]:
            pmids.union(ClinvarPubmeds('%s' % seqvar))
    return pmids
    

def pubtator_hgvs_to_pmid(hgvs_lex_or_text):
    lex = _guard_lex(hgvs_lex_or_text)
    edittype = HgvsComponents(lex.seqvar).edittype

    if edittype not in ['SUB', 'DEL', 'INS', 'FS', 'INDEL']:
        log.info('[%s] Cannot process edit type %s' % (hgvs_text, edittype))
        return None

    try:
        gene_id = GeneID(lex.gene_name)
    except TypeError:
        # no gene_name? it happens.
        gene_id = None

    log.info('[%s]' % lex.seqvar, lex.gene_name, '(Gene ID: %s)' % gene_id)

    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype]:
            try:
                components = HgvsComponents(seqvar)
            except RejectedSeqVar:
                log.debug('[%s] Rejected sequence variant: %r' % (lex.seqvar, seqvar))
                continue

            log.info('[%s]' % lex.seqvar, seqtype, components)
            if seqtype == 'p':
                results = pubtator_db.search_proteins(components, gene_id)
            else:
                results = pubtator_db.search_m2p(components, gene_id)

            for res in results:
                pmids.add(res['PMID'])

    return list(pmids)



#### API classes


ClinvarCache = SQLCache('clinvarpubmeds')
ClinvarCache.create_table()

PubtatorCache = SQLCache('pubtatorpubmeds')
PubtatorCache.create_table()

NCBIVariantReporterCache = SQLCache('ncbipubmeds')
NCBIVariantReporterCache.create_table()
