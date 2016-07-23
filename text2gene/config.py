from __future__ import absolute_import, unicode_literals

import os
from configparser import ConfigParser

CWD = os.path.dirname(os.path.realpath(__file__))

PKGNAME = 'text2gene'
default_cfg_dir = os.path.join(CWD, 'config')
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

private_conf = os.path.join(CFGDIR, 'private.ini')
if os.path.exists(private_conf):
    print('Found text2gene/config/private.ini')
    CONFIG.read(private_conf)

# if training is "active", enable GRANULAR_CACHE for all cacheing engines.
GRANULAR_CACHE = False
