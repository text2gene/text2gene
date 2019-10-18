### IMPORTANT: this file doesn't work with modern Fabfile.  See Issue #4.
### https://github.com/text2gene/text2gene/issues/4

import os
import logging
from configparser import ConfigParser

from fabric.operations import put, local
from fabric.decorators import task
from fabric.api import cd, run, env, sudo, local

# TODO: solution for including API keys (NCBI, Google, etc)

os.environ.setdefault('UTA_HOST', 'localhost')
os.environ.setdefault('UTA_USER', 'uta_admin')

ENV = os.getenv('text2gene_ENV', 'dev')

env.user = 'nthmost'

@task
def run_private():
    cfg = ConfigParser()
    cfg.read('text2gene/config/private.ini')
    host = cfg.get('network', 'host')
    port = cfg.get('network', 'port')
    num_workers = cfg.get('gunicorn', 'num_workers')
    local('gunicorn -w %s -b %s:%s wsgi:app' % (num_workers, host, port))


@task
def run_services():
    # show_envs()
    cfg = ConfigParser()
    cfg.read('text2gene/config/%s.ini' % ENV.lower())
    host = cfg.get('network', 'host')
    port = cfg.get('network', 'port')
    num_workers = cfg.get('gunicorn', 'num_workers')
    local('gunicorn -w %s -b %s:%s wsgi:app' % (num_workers, host, port))

