import glob, os

from setuptools import setup, find_packages

setup(
    name = 'pubtatordb',
    version = '0.0.1',
    description = 'Pubtator database interaction layer',
    author = 'Naomi Most',
    maintainer = 'Naomi Most',
    author_email = 'naomi@nthmost.com',
    maintainer_email = 'naomi@nthmost.com',
    license = 'Apache 2.0',
    packages = find_packages(),
    install_requires = [
        'setuptools',
        # 'mysqlclient',  # py3k only
        'pysqlpool',      # py2k only
        'pytz',
        'pyrfc3339',
        ],
    )
