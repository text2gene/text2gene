import logging

from metavariant import Variant
from text2gene.experiment import Experiment

experiment_name = 'monarch_fanconis_anemia'
iteration = 132

fh = logging.FileHandler('%s.%i.log' % (experiment_name, iteration))
log = logging.getLogger('text2gene.experiment')
log.addHandler(fh)

otherlog = logging.getLogger('text2gene')
otherlog.addHandler(logging.StreamHandler())
otherlog.setLevel(logging.DEBUG)

sample_sheet = open('data/monarch_fanconis_anemia_131.tsv').read().split('\n')
LOADED_EXAMPLES = []
for line in sample_sheet:
    try:
        seqvar = Variant(line.split()[1])
    except Exception as error:
        print(error)
        continue

    if seqvar:
        LOADED_EXAMPLES.append('%s' % seqvar)


exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                    hgvs_examples=LOADED_EXAMPLES,)
exper.run()

