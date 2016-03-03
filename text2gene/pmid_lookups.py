from __future__ import absolute_import, print_function, unicode_literals

from medgen.api import GeneID

from pubtatordb import PubtatorDB
from hgvs_lexicon import HgvsLVG, HgvsComponents, RejectedSeqVar

from .config import log

pubtator_db = PubtatorDB()


#def clinvar_hgvs_to_pmid(hgvs_text):


def pubtator_hgvs_to_pmid(hgvs_text):

    lex = HgvsLVG(hgvs_text)
    edittype = HgvsComponents(lex.seqvar).edittype

    if edittype not in ['SUB', 'DEL', 'INS', 'FS', 'INDEL']:
        log.info('[%s] Cannot process edit type %s' % (hgvs_text, edittype))
        return None

    try:
        gene_id = GeneID(lex.gene_name)
    except TypeError:
        # no gene_name? it happens.
        gene_id = None

    log.info('[%s]' % hgvs_text, lex.gene_name, '(Gene ID: %s)' % gene_id)

    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype]:
            try:
                components = HgvsComponents(seqvar)
            except RejectedSeqVar:
                log.debug('[%s] Rejected sequence variant: %r' % (hgvs_text, seqvar))
                continue

            log.info('[%s]' % hgvs_text, seqtype, components)
            if seqtype == 'p':
                results = pubtator_db.search_proteins(components, gene_id)
            else:
                results = pubtator_db.search_m2p(components, gene_id)

            for res in results:
                pmids.add(res['PMID'])

    return list(pmids)
