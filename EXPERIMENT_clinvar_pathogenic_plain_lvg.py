import logging

experiment_name = 'clinvar_pathogenic_plain_lvg'
iteration = 1

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())

from text2gene.training import Experiment
exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                        hgvs_examples_table = 'hgvs_citations_pathogenic',
                        hgvs_examples_db = 'clinvar',
                  )
exper.run()

