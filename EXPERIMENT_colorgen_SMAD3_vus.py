import logging

from metavariant import Variant
from text2gene.experiment import Experiment

experiment_name = 'EXP_colorgen_SMAD3_vus'
iteration = 2

datafile = 'data/colorgen_SMAD3_vus.tsv'

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())
otherlog.setLevel(logging.DEBUG)

LOADED_EXAMPLES = set()
for item in open(datafile).read().split('\n'):
    LOADED_EXAMPLES.add(item.strip())

print(len(LOADED_EXAMPLES), 'samples loaded from', datafile)

exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                    hgvs_examples=LOADED_EXAMPLES, gene_name='SMAD3')
exper.run()

