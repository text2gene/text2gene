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
    name = 'pubtatordb',
    version = '0.0.1',
    description = 'Pubtator database interaction layer',
    author = 'Naomi Most',
    maintainer = 'Naomi Most',
    author_email = 'naomi@nthmost.com',
    maintainer_email = 'naomi@nthmost.com',
    license = 'Apache 2.0',
    packages = find_packages(),
    entry_points = { 'console_scripts': [
                            'hgvs_string_lookup = text2gene.__main__:process_one_from_command_line',
                            'hgvs_file_lookup = text2gene.__main__:process_many_from_command_line', 
                            'hgvs2pmid = text2gene.__main__:cli_hgvs2pmid',
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
        'flask',  # web api
        'gunicorn',  # web api
        'fabric',  # web api
        ],
    )
