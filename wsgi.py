from __future__ import absolute_import, print_function
import logging
import os

CWD = os.path.dirname(os.path.realpath(__file__))

# Activate working environment upon startup. See:
# http://flask.pocoo.org/docs/0.11/deploying/mod_wsgi/#working-with-virtual-environments
activate_this = os.path.join(CWD, './ve/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))


from werkzeug.contrib.fixers import ProxyFix

from text2gene.app_config import app
from text2gene.config import CFGDIR, ENV, PKGNAME, CONFIG

from requests.packages import urllib3
urllib3.disable_warnings()

filepath = os.path.join(CWD, 'logs/text2gene_service.log')
fh = logging.FileHandler(filepath)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)

log = logging.getLogger(PKGNAME)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

logging.getLogger('metavariant').addHandler(fh)
logging.getLogger('metapub').addHandler(fh)
logging.getLogger('metapub').setLevel(logging.DEBUG)


app.wsgi_app = ProxyFix(app.wsgi_app) 

def show_envs():
    relevant_envs = [ '%s_ENV' % PKGNAME, 
                      '%s_CONFIG_DIR' % PKGNAME,
                      '%s_DEBUG' % PKGNAME]
    print('Config files in %s' % CFGDIR)
    print('Using %s.ini' % ENV)
    print('Relevant environment variable settings:')
    print_tmpl = '     %s: %s'
    for env in relevant_envs:
        print(print_tmpl % (env, os.getenv(env, 'not set')))

if __name__=='__main__':
    show_envs()
    app.run(debug=True, host='0.0.0.0', port=int(CONFIG.get('network', 'port')))

