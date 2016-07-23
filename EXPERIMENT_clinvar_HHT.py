import logging

from metavariant import Variant
from text2gene.experiment import Experiment

experiment_name = 'clinvar_hht'
iteration = 1

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())
otherlog.setLevel(logging.DEBUG)

exper = Experiment(experiment_name, iteration=iteration,
                   hgvs_examples_table = 'samples_hht',
                   hgvs_examples_db = 'clinvar',
                  )
exper.run()

