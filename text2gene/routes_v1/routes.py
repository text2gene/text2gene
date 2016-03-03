from __future__ import absolute_import, print_function

API_INDICATOR = 'v1'

import logging, json, os, sys

#from flask import Flask, render_template, Response, request
from flask import Blueprint

routes_v1 = Blueprint('routes_v1', __name__, template_folder='templates')

from medgen.api import NCBIVariantReport

from hgvs_lexicon import HgvsLVG

# a weird one from N-of-1:
#NM_194248.1:c.158C>T

from ..config import CONFIG, ENV, PKGNAME
from ..utils import HTTP200, HTTP400

log = logging.getLogger('%s.routes_v1' % PKGNAME)


@routes_v1.route('/v1/ncbi/<hgvs_text>')
def ncbi_variant_reporter(hgvs_text):
    """ Takes an input hgvs_text and uses NCBI Variant Reporter to retrieve and display
    data related to this genetic variant.

    :param hgvs_text: str
    :return: HTTP200 (json) or HTTP400 (json)
    """
    outd = {'action': 'ncbi', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        preamble, results_dict = NCBIVariantReport(hgvs_text)

        outd['response'] = {'preamble': preamble, 'data': results_dict}

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
