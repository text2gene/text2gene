from __future__ import absolute_import

import os
import logging
from configparser import ConfigParser

from fabric.operations import put, local
from fabric.decorators import task
from fabric.api import cd, run, env, sudo, local

os.environ.setdefault('UTA_HOST', 'localhost')
os.environ.setdefault('UTA_USER', 'uta_admin')

#from wsgi import show_envs, PKGNAME

#ENV = os.getenv('%s_SERVICES_ENV' % PKGNAME, 'dev')

env.user = 'nthmost'

#@task
#def preset_envs():
#    os.environ['%s_SERVICES_ENV' % PKGNAME] = 'dev'
#    os.environ['%s_SERVICES_CONFIG_DIR' % PKGNAME] = 'etc'
#    os.environ['%s_SERVICES_DEBUG' % PKGNAME] = 'True'

@task
def run_services():
    #preset_envs()
#    show_envs()
    cfg = ConfigParser()
    cfg.read('fab.conf')
    host = cfg.get('network', 'host')
    port = cfg.get('network', 'port')
    num_workers = cfg.get('gunicorn', 'num_workers')

    local('gunicorn -w %s -b %s:%s wsgi:app' % (num_workers, host, port))

