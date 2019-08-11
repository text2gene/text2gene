import logging

experiment_name = 'clinvar_samples_nogoogle'
iteration = 1

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())

from text2gene.experiment import Experiment
exper = Experiment(experiment_name, lvg_mode='ncbi_enriched', iteration=iteration,
                        hgvs_examples_table = 'samples',
                        hgvs_examples_db = 'clinvar',
                        search_modules = ['pubtator', 'clinvar', 'ncbi'],
                  )
exper.run()

