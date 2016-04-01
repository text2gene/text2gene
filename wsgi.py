from __future__ import absolute_import, print_function

import os
from werkzeug.contrib.fixers import ProxyFix

from text2gene.app_config import app
from text2gene.config import CFGDIR, ENV, PKGNAME, CONFIG

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
    app.run(debug=True, host='0.0.0.0', port=int(CONFIG.get('flask', 'port')))

