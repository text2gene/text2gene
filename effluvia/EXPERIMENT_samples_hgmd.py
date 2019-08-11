import logging

experiment_name = 'EXP_hgmd_samples'
iteration = 1

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())

from text2gene.experiment import Experiment
exper = Experiment(experiment_name, lvg_mode='ncbi_enriched', iteration=iteration,
                        hgvs_examples_table = 'samples_hgmd',
                        hgvs_examples_db = 'clinvar',
                  )
exper.run()

