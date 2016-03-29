import glob, os

from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext as _build_ext

class build_ext(_build_ext):
    # http://stackoverflow.com/questions/21605927/why-doesnt-setup-requires-work-properly-for-numpy/21621493
    def finalize_options(self):
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process:
        __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())

setup(
    name = 'text2gene',
    version = '0.0.2',
    description = 'genetic variant lvg and medical genetics search for relevant literature',
    author = 'Naomi Most',
    maintainer = 'Naomi Most',
    author_email = 'naomi@nthmost.com',
    maintainer_email = 'naomi@nthmost.com',
    license = 'Apache 2.0',
    packages = find_packages(),
    entry_points = { 'console_scripts': [
                            'hgvs_search_pubtator = text2gene.__main__:cli_pubtator_search_string',
                            'hgvsfile_search_pubtator= text2gene.__main__:cli_pubtator_search_file', 
                            'hgvs2pmid = text2gene.__main__:cli_hgvs2pmid',
                            'hgvsfile2pmid = text2gene.__main__:cli_hgvsfile2pmid',
                            ] 
                   },
    cmdclass = {'build_ext': build_ext},
    setup_requires = ['setuptools', 'numpy'],
    install_requires = [
        # 'mysqlclient',  # py3k only
        'pysqlpool',      # py2k only
        'pytz',
        'pyrfc3339',
        'numpy',
        'biopython',
        'uta',
        'hgvs',
        'medgen',
        'requests',  # ncbi and google query retrieval
        'flask',  # web api
        'gunicorn',  # web api
        'fabric',  # web api
        'ipython', # cli / debug tool
        ],
    )
