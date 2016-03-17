from __future__ import absolute_import, print_function, unicode_literals

from .api import ClinvarHgvs2Pmid, PubtatorHgvs2Pmid, NCBIHgvsLVG, NCBIHgvs2Pmid

# not yet using: NCBIEnrichedLVG


class Experiment(object):

    def __init__(self, experiment_name, **kwargs):
        self.experiment_name = experiment_name

        self.iteration = kwargs.get('iteration', 0)

        self.hgvs_examples_table = kwargs.get('hgvs_examples_table', 'hgvs_examples')
        self.hgvs_examples_db = kwargs.get('hgvs_examples_db', 'clinvar')

        
