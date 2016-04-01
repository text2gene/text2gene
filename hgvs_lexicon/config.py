from __future__ import absolute_import, unicode_literals

import os, socket
from configparser import ConfigParser

import hgvs.dataproviders.uta

PKGNAME = 'hgvs_lexicon'
default_cfg_dir = os.path.join(os.getcwd(), 'etc')
CFGDIR = os.getenv('%s_CONFIG_DIR' % PKGNAME, default_cfg_dir)
DEBUG = bool(os.getenv('%s_DEBUG' % PKGNAME, False))
ENV = os.getenv('%s_ENV' % PKGNAME, 'dev')

####
import logging
log = logging.getLogger(PKGNAME)
if DEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)
####

log.debug('%s config dir: %s' % (PKGNAME, CFGDIR))
log.debug('%s env: %s' % (PKGNAME, ENV))

configs = [os.path.join(CFGDIR, x) for x in os.listdir(CFGDIR) if x.find(ENV+'.ini') > -1]

CONFIG = ConfigParser()
CONFIG.read(configs)

def get_uta_connection():
    """ Returns an open UTA connection to the first available UTA host, as prioritized
    in the config file (see uta_* items under the [hgvs] section).

    If no connection can be made, returns None.

    :return: open UTA connection or None if all connections fail
    """

    # try default UTA host; fall back to alternate UTA host if timeout occurs.

    hosts = [CONFIG.get('hgvs', 'uta_default_host'), CONFIG.get('hgvs', 'uta_fallback_host')]
    timeout = int(CONFIG.get('hgvs', 'uta_connection_timeout'))
    uta_cnxn_tmpl = CONFIG.get('hgvs', 'uta_connection_tmpl')
    port = 5432

    for host in hosts:
        if host == 'default':
            return hgvs.dataproviders.uta.connect()
        else:
            try:
                socket.create_connection((host, port), timeout=timeout)
                log.info('Connected to UTA host %s on port %i', host, port)
                return hgvs.dataproviders.uta.connect(uta_cnxn_tmpl.format(host=host), pooling=True)
            except socket.timeout:
                log.info('Could not connect to UTA host %s on port %i.', host, port)

    # if we get this far and nothing can be reached, return the biocommons default UTA host
    return hgvs.dataproviders.uta.connect()
