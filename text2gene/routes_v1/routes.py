from __future__ import absolute_import, print_function, unicode_literals

API_INDICATOR = 'v1'

import logging

from flask import Blueprint
from hgvs.exceptions import HGVSParseError

from medgen.api import NCBIVariantReport
from hgvs_lexicon import HgvsLVG

from ..cached import PubtatorHgvs2Pmid, NCBIHgvs2Pmid, ClinvarHgvs2Pmid
from ..config import CONFIG, ENV, PKGNAME
from ..utils import HTTP200, HTTP400

routes_v1 = Blueprint('routes_v1', __name__, template_folder='templates')

log = logging.getLogger('%s.routes_v1' % PKGNAME)


@routes_v1.route('/v1/hgvs2pmid/<hgvs_text>')
def hgvs2pmid(hgvs_text):
    """ Takes an input hgvs_text and uses a combination of methods to name pubmed
    articles by their PMID that mention this genetic variant.

        # a weird one from N-of-1:
        #NM_194248.1:c.158C>T

    :param hgvs_text: str
    :return: HTTP200 (json) or HTTP400 (json)
    """
    outd = {'action': 'hgvs2pmid', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            lex = HgvsLVG(hgvs_text)
        except HGVSParseError as error:
            return HTTP400(error, 'Cannot parse input string %s as hgvs text' % hgvs_text)

        outd['lvg'] = lex.to_dict()

        outd['response'] = { }

        ncbi_pmids = NCBIHgvs2Pmid(hgvs_text)
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
    outd = {'action': 'ncbi', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        report = NCBIVariantReport(hgvs_text)

        outd['response'] = report

    return HTTP200(outd)


@routes_v1.route('/v1/lvg/<hgvs_text>')
def lvg(hgvs_text):
    """ Takes an input hgvs_text and generates valid HGVS alternative statements. 
        Returns JSON (http 200).  If problem w/ HGVS string, responds with http 400"""

    outd = {'action': 'lvg', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            hgvs_obj = HgvsLVG(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error using HgvsLVG to find lexical variants for %s' % hgvs_text)
        outd['response'] = hgvs_obj.to_dict()
    
    return HTTP200(outd)
