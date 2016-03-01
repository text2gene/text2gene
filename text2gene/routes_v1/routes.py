from __future__ import absolute_import, print_function

API_INDICATOR = 'v1'

import logging, json, os, sys

import configparser

from flask import Flask, render_template, Response, request
from flask import Blueprint

routes_v1 = Blueprint('routes_v1', __name__, template_folder='templates')

from hgvs_lexicon import HgvsLVG

from ..config import CONFIG, ENV, PKGNAME
from ..utils import HTTP200, HTTP400
#from ..validators import validate_email, validate_pmid

log = logging.getLogger('%s.routes_v1' % PKGNAME)


@routes_v1.route('/v1/lvg/<hgvs_text>')
def lvg(hgvs_text):
    """ Takes an input hgvs_text and generates valid HGVS alternative statements. 
        Returns JSON (http 200).  If problem w/ HGVS string, responds with http 400"""

    outd = {'action': 'lvg', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            hgvs_obj = HgvsLVG(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'finding lexical variants for %s' % hgvs_text)
        outd['response'] = hgvs_obj.to_dict()
    
    return HTTP200(outd)


### DEMO ROUTE(S) for sanity checking below

@routes_v1.route('/%s/echo/<inp>' % API_INDICATOR)
def echo(inp=None):
    '''Any input it receives, it prints back to you, but in JSON (ooh)!'''
    if inp == '%3Cinp%3E':
        return HTTP200({'action': 'echo', 'input': inp, 'response': 'Change <inp> in url to another input string.'})
    else:
        return HTTP200({'action': 'echo', 'input': inp, 'response': inp})
    
