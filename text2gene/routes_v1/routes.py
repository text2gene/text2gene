from __future__ import absolute_import, unicode_literals

API_INDICATOR = 'v1'

import logging

from flask import Blueprint, request

from hgvs_lexicon.exceptions import CriticalHgvsError

from ..lvg_cached import LVG
from ..googlequery import GoogleQuery, query_cse_return_items
from ..ncbi import NCBIHgvs2Pmid, NCBIReport, LVGEnriched
from ..cached import PubtatorHgvs2Pmid, ClinvarHgvs2Pmid
from ..config import PKGNAME
from ..utils import HTTP200, HTTP400

routes_v1 = Blueprint('routes_v1', __name__, template_folder='templates')

log = logging.getLogger('%s.routes_v1' % PKGNAME)


@routes_v1.route('/v1/hgvs2pmid/<hgvs_text>')
def hgvs2pmid(hgvs_text):
    """ Takes an input hgvs_text and uses a combination of methods to name pubmed
    articles by their PMID that mention this genetic variant.

        # a weird one:
        #NM_194248.1:c.158C>T

    :param hgvs_text: str
    :return: HTTP200 (json) or HTTP400 (json)
    """
    # TODO: allow URL argument to specify type of lvg_mode to use.

    outd = {'action': 'hgvs2pmid', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            lex = LVGEnriched(hgvs_text)
        except CriticalHgvsError as error:
            return HTTP400(error, 'Cannot parse input string %s as hgvs text' % hgvs_text)

        outd['lvg'] = lex.to_dict()

        outd['response'] = {}

        ncbi_pmids = NCBIHgvs2Pmid(lex.hgvs_text)
        if ncbi_pmids:
            outd['response']['NCBI'] = ncbi_pmids

        clinvar_pmids = ClinvarHgvs2Pmid(lex)
        if clinvar_pmids:
            outd['response']['ClinVar'] = clinvar_pmids

        pubtator_pmids = PubtatorHgvs2Pmid(lex)
        if pubtator_pmids:
            outd['response']['PubTator'] = pubtator_pmids

    return HTTP200(outd)


@routes_v1.route('/v1/report/<hgvs_text>')
def ncbi_variant_reporter(hgvs_text):
    """ Takes an input hgvs_text and uses NCBI Variant Reporter to retrieve and display
    data related to this genetic variant.

    :param hgvs_text: str
    :return: HTTP200 (json) or HTTP400 (json)
    """
    outd = {'action': 'report', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        report = NCBIReport(hgvs_text)

        outd['response'] = report

    return HTTP200(outd)


@routes_v1.route('/v1/lvgenriched/<hgvs_text>')
def lvg_enriched(hgvs_text):
    """ Takes an input hgvs_text and generates valid HGVS alternative statements,
    using a pre-enrichment process of seeding HgvsLVG with variants from the NCBI Variation Reporter.

    Returns JSON (http 200).  If problem w/ HGVS string, responds with http 400
    """

    outd = {'action': 'lvgenriched', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            hgvs_obj = LVGEnriched(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error using HgvsLVG to find lexical variants for %s' % hgvs_text)
        outd['response'] = hgvs_obj.to_dict()

    return HTTP200(outd)


@routes_v1.route('/v1/lvg/<hgvs_text>')
def lvg(hgvs_text):
    """ Takes an input hgvs_text and generates valid HGVS alternative statements. 
        Returns JSON (http 200).  If problem w/ HGVS string, responds with http 400
    """

    outd = {'action': 'lvg', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            hgvs_obj = LVG(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error using HgvsLVG to find lexical variants for %s' % hgvs_text)
        outd['response'] = hgvs_obj.to_dict()
    
    return HTTP200(outd)


@routes_v1.route('/v1/google', methods=['POST'])
@routes_v1.route('/v1/google/<hgvs_text>', methods=['GET'])
def google_query(hgvs_text='<hgvs_text>', **kwargs):
    """ Performs LVG and GoogleQuery for given hgvs_text string.

    Available keywords:
            cse: 'whitelist' or 'schema'
            seqtypes: any combination of c,p,g,n (comma-separated list)

    :return: json including text of built query and structured data of Google response
    """

    if request.method == 'POST':
        hgvs_text = request.form.get('hgvs_text')
        seqtypes = request.form.getlist('seqtypes')
        cse = request.form.get('cse')
        log.debug('POST form contained: hgvs_text=%s, seqtypes=%s, cse=%s' % (hgvs_text, ','.join(seqtypes), cse))
        return redirect(
            '/%s/google/%s?seqtypes=%s&types=%s&cse=%s' % (API_INDICATOR, hgvs_text, ','.join(seqtypes), cse), code=302)

    else:
        hgvs_text = hgvs_text.strip()
        seqtypes = request.args.get('seqtypes', 'c,p,g,n').split(',')
        cse = request.args.get('cse', 'whitelist')


    outd = {'action': 'google', 'hgvs_text': hgvs_text, 'cse': cse,
            'seqtypes': seqtypes,
            'query': '',
            'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            lex = LVGEnriched(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error before building query: could not build LVG object for %s.' % hgvs_text)

        gq = GoogleQuery(lex)

        outd['query'] = gq.build_query(outd['seqtypes'])

        outd['response'] = []
        for res in gq.query(outd['query']):
            outd['response'].append(res.to_dict())

    return HTTP200(outd)
