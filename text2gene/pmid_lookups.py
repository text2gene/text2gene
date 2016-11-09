from __future__ import absolute_import, unicode_literals

from medgen.api import GeneID, ClinvarPubmeds
from metavariant import VariantComponents, Variant
from metavariant.exceptions import RejectedSeqVar

from aminosearch import PubtatorDB
from aminosearch.exceptions import PubtatorDBError

from .config import log

pubtator_db = PubtatorDB()


def clinvar_lex_to_pmid(lex):
    """ Takes a "lex" object (one of VariantLVG, NCBIHgvsLVG, or NCBIEnrichedLVG) and uses each variant found in
    lex.variants to do a search in Clinvar for associated PMIDs.  Returns a list of PMIDs.

    :param lex: lexical variant object (see above options)
    :return: list of pmids found in Clinvar
    """
    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype].values():
            # throw away sequence variants without enough information
            try:
                VariantComponents(seqvar)
            except RejectedSeqVar:
                log.debug('[%s] Rejected sequence variant: %r' % (lex.seqvar, seqvar))
                continue

            for pmid in ClinvarPubmeds('%s' % seqvar):
                pmids.add(int(pmid))
    return list(pmids)
    

def pubtator_lex_to_pmid(lex):
    """ Takes an LVG object ("lex") (one of VariantLVG, NCBIHgvsLVG, or NCBIEnrichedLVG) and uses each
    variant found in lex.variants to do a search in PubTator for associated PMIDs.

    Returns a dictionary of results mapping VariantComponents objects to PMIDs found -- i.e.:

        { hgvs_text: {'comp': VariantComponents object,
                      'pmids': [<pmids>]
                     }

    :param lex: lexical variant object (see above options)
    :return: dictionary of results
    """
    try:
        gene_id = GeneID(lex.gene_name)
    except TypeError:
        # no gene_name? it happens -- but our results will be basically bunk without it.
        return []

    log.info('[%s] %s (Gene ID: %s)', lex.seqvar, lex.gene_name, gene_id)

    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype].values():
            try:
                components = VariantComponents(seqvar)
            except RejectedSeqVar:
                log.debug('[%s] Rejected sequence variant: %r' % (lex.seqvar, seqvar))
                continue

            log.info('[%s] [[%s]] %s', lex.seqvar, seqvar, components)
            try:
                if seqtype == 'p':
                    results = pubtator_db.search_proteins(components, gene_id)
                else:
                    results = pubtator_db.search_m2p(components, gene_id)
                for res in results:
                    pmids.add(int(res['PMID']))
            except PubtatorDBError as error:
                log.info('[%s] (%s) %r', lex.seqvar, seqvar, error)

    return list(pmids)


def pubtator_results_for_seqvar(seqvar_or_hgvs_text, gene_id):
    """ Takes a SequenceVariant or hgvs_text string.
    Returns a dictionary of results mapping hgvs_text to a list of results from pubtator, i.e.:

        { hgvs_text: [ <dictionaries representing matching results from pubtator> ] }

    :param seqvar_or_hgvs_text: hgvs_text or SequenceVariant object
    :param gene_id: id of gene associated with variant (required)
    :return: dictionary of results
    :raises: RejectedSeqVar, PubtatorDBError
    """
    seqvar = Variant(seqvar_or_hgvs_text)
    hgvs_text = '%s' % seqvar

    result = {hgvs_text: []}

    components = VariantComponents(seqvar)

    if seqvar.type == 'p':
        result[hgvs_text] = pubtator_db.search_proteins(components, gene_id)
    else:
        result[hgvs_text] = pubtator_db.search_m2p(components, gene_id)

    return result


def pubtator_results_for_lex(lex):
    """ Takes an LVG object ("lex") (one of VariantLVG, NCBIHgvsLVG, or NCBIEnrichedLVG) and uses each
    variant found in lex.variants to do a search in PubTator for associated PMIDs.

    Returns a dictionary of results mapping hgvs_text to PMIDs found -- i.e.:

        { hgvs_text: {'components': VariantComponents object,
                      'pmids': [<pmids>]
                     }
        }

    :param lex: lexical variant object (VariantLVG, NCBIHgvsLVG, NCBIEnrichedLVG)
    :return: dictionary of results
    """
    try:
        gene_id = GeneID(lex.gene_name)
    except TypeError:
        # no gene_name? it happens -- but our results will be basically bunk without it.
        return {}

    log.info('[%s] %s (Gene ID: %s)', lex.seqvar, lex.gene_name, gene_id)

    results = {}
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype].values():

            try:
                result = pubtator_results_for_seqvar(seqvar, gene_id)
                results.update(result)
                try:
                    for row in results['%s' % seqvar]:
                        log.info('[%s] [[%s]] Mentions: %s  PMID: %s  Components: %s', lex.seqvar, seqvar,
                                  row['Mentions'], row['PMID'], row['Components'])
                except Exception as error:
                    print(error)
                    #from IPython import embed; embed()

            except RejectedSeqVar:
                log.debug('[%s] [[%s]] VariantComponents raised RejectedSeqVar', lex.seqvar, seqvar)

            except PubtatorDBError as error:
                log.info('[%s] [[%s]] %r', lex.seqvar, seqvar, error)

    return results
