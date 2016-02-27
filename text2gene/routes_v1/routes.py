from __future__ import absolute_import, print_function

API_INDICATOR = 'v1'

import logging, json, os, sys

import configparser

from flask import Flask, render_template, Response, request
from flask import Blueprint

routes_v1 = Blueprint('routes_v1', __name__, template_folder='templates')

from ..config import CONFIG, ENV, PKGNAME
from ..utils import HTTP200, HTTP400
#from ..validators import validate_email, validate_pmid

log = logging.getLogger('%s.routes_v1' % PKGNAME)

@routes_v1.route('/%s/echo/<inp>' % API_INDICATOR)
def echo(inp=None):
    '''Any input it receives, it prints back to you, but in JSON (ooh)!'''
    if inp == '%3Cinp%3E':
        return HTTP200({'action': 'echo', 'input': inp, 'response': inp})
    else:
        return HTTP200({'action': 'echo', 'input': inp, 'response': 'Change <inp> in url to another input string.'})
    
