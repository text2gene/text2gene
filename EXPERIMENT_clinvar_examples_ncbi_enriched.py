import logging

experiment_name = 'clinvar_examples_ncbi_enriched'

fh = logging.FileHandler(experiment_name + ".log")
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())

from text2gene.training import Experiment
exper = Experiment(experiment_name, lvg_mode='ncbi_enriched')
exper.run()

