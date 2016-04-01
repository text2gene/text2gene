import os
import logging

from fabric.operations import put, local
from fabric.decorators import task
from fabric.api import cd, run, env, sudo, local

from wsgi import show_envs, PKGNAME

ENV = os.getenv('%s_SERVICES_ENV' % PKGNAME, 'dev')

env.user = 'biomed'

ch = logging.StreamHandler()
logging.getLogger('hgvs_lexicon').addHandler(ch)

@task
def preset_envs():
    os.environ['%s_SERVICES_ENV' % PKGNAME] = 'dev'
    os.environ['%s_SERVICES_CONFIG_DIR' % PKGNAME] = 'etc'
    os.environ['%s_SERVICES_DEBUG' % PKGNAME] = 'True'

@task
def run_services():
    #preset_envs()
    show_envs()
    local('gunicorn -w 5 -b 0.0.0.0:5000 wsgi:app')

