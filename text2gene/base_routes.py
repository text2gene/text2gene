from __future__ import print_function, absolute_import

from flask import Blueprint, render_template

from .utils import HTTP200, HTTP400, get_hostname
from .config import ENV, CONFIG, PKGNAME

base = Blueprint('base', __name__, template_folder='templates')

@base.route('/')
def home():
    return render_template('home.html') 

@base.route('/about')
def about():
    return render_template('about.html')

@base.route('/examples')
def examples():
    api_version = CONFIG.get('api', 'latest_version')
    hgvs_samples = ['NM_014855.2:c.333G>C', 'NM_001126115.1:c.318T>G', 'NM_005228.3:c.2240_2257del18']
    return render_template('examples.html', hgvs_samples=hgvs_samples, api_version=api_version)

@base.route('/OK')
def OK():
    return HTTP200({ 'service': '%s' % PKGNAME, 
                     'ENV': '%s' % ENV,
                     'hostname': '%s' % get_hostname(),
                     'api_latest_version': CONFIG.get('api', 'latest_version'), 
                     'api_supported_versions': CONFIG.get('api', 'supported_versions'),
                   })

