import logging

experiment_name = 'clinvar_pathogenic_plain_lvg'
iteration = 1

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

ch = logging.StreamHandler()

sqlcache_log = logging.getLogger('text2gene.sqlcache')
sqlcache_log.setLevel(logging.DEBUG)

otherlog = logging.getLogger('text2gene')

otherlog.addHandler(ch)
sqlcache_log.addHandler(ch)

from text2gene.training import Experiment
exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                        hgvs_examples_table = 'hgvs_citations_pathogenic',
                        hgvs_examples_db = 'clinvar',
                  )
exper.run()

