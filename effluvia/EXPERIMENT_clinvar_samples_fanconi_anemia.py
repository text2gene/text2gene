import logging
import os

experiment_name = 'clinvar_samples_fanconi_anemia'
iteration = 1

logdir = 'logs'
fh = logging.FileHandler(os.path.join(logdir, '%s.%i.log' % (experiment_name, iteration)))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())

from text2gene.experiment import Experiment
exper = Experiment(experiment_name, lvg_mode='ncbi_enriched', iteration=iteration,
                        hgvs_examples_table = 'samples_fanconi_anemia',
                        hgvs_examples_db = 'clinvar',
                  )
                        #search_modules = ['pubtator', 'clinvar', 'ncbi'],
exper.run()

