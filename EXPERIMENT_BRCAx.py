import logging

from metavariant import Variant
from text2gene.experiment import Experiment

experiment_name = 'BRCAx'
iteration = 1

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())
otherlog.setLevel(logging.DEBUG)

LOADED_EXAMPLES = open('data/samples_BRCAx.tsv').readlines()

exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                    hgvs_examples=LOADED_EXAMPLES,)
exper.run()

