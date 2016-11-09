PKGNAME = 'pubtatordb'
DATABASE = { 'host': 'localhost', 'user': 'medgen', 'pass': 'medgen', 'name': 'PubTator' }

SQLDEBUG = True

import logging

log = logging.getLogger('pubtatordb')

def get_process_log(filepath, loglevel=logging.INFO, name=PKGNAME+'-process'):
    log = logging.getLogger(name)
    log.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(filepath)
    fh.setFormatter(formatter)
    fh.setLevel(loglevel)
    log.addHandler(fh)
    return log


def get_data_log(filepath, name=PKGNAME+'-data'):
    datalog = logging.getLogger(name)
    datalog.setLevel(logging.DEBUG)
    datalog.propagate = False
    formatter = logging.Formatter('')
    fh = logging.FileHandler(filepath)
    fh.setFormatter(formatter)
    datalog.addHandler(fh)
    return datalog

