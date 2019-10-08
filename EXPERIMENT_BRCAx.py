import logging

from metavariant import Variant
from text2gene.experiment import Experiment

experiment_name = 'BRCAx'
iteration = 1

datafile = 'data/samples_BRCAx.tsv'

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())
otherlog.setLevel(logging.DEBUG)

LOADED_EXAMPLES = set()
for item in open(datafile).readlines():
    LOADED_EXAMPLES.add(item)

exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                    hgvs_examples=LOADED_EXAMPLES,)
exper.run()

