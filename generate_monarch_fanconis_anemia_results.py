from __future__ import print_function, unicode_literals

import logging
import re

from metavariant import Variant
from text2gene.experiment import Experiment

experiment_name = 'monarch_fanconis_anemia'
iteration = 131

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


def get_known_pmids_from_line(line):
    """ClinVarVariant:41224    NM_004629.1(FANCG):c.1183_1192delGAGGTGTTTT (p.Glu395Trpfs)     NCBITaxon:9606  Homo sapiens                    GENO:0000840    pathogenic_for_condition        OMIM:614082     Fanconi anemia, complementation group G                         http://data.monarchinitiative.org/ttl/clinvar.ttl       direct"""
    re_pmids = re.compile('PMID:(?P<pmid>\d+)')
    return re_pmids.findall(line)


exper = Experiment(experiment_name, lvg_mode='lvg', iteration=iteration,
                    hgvs_examples=LOADED_EXAMPLES,)
sql = 'select hgvs_text, PMID from ' + exper.summary_table_name + ' where hgvs_text=%s'

output_sheet = open('data/monarch_fanconis_anemia_RESULTS.tsv', 'w')
parsed = 0
found = 0
unparsed = 0
nopmids = 0
newpmids = 0
hadzero = 0

# make a new header with a text2gene_evidence column
output_sheet.write(sample_sheet[0] + '\ttext2gene_evidence\n')

for line in sample_sheet[1:]:
    try:
        seqvar = Variant(line.split()[1])
    except Exception as error:
        continue

    rows = None
    if seqvar:
        print(line.split()[1] + ' parsed')
        parsed += 1
        rows = exper.fetchall(sql, '%s' % seqvar)
        if rows:
            found += 1
            known_pmids = get_known_pmids_from_line(line)
            t2g_pmids = [str(int(item['PMID'])) for item in rows]
            new_pmids = []
            for pmid in t2g_pmids:
                if pmid not in known_pmids:
                    new_pmids.append(pmid)
            if new_pmids:
                if len(known_pmids) == 0:
                    hadzero += 1
                newpmids += 1
                pmid_str = '|'.join(['PMID:%s' % item for item in new_pmids])
                line = line + '\t' + pmid_str
            else:
                nopmids += 1
                line = line + '\t '
        else:
            nopmids += 1
            line = line + '\t '
    else:
        unparsed += 1
        print(line.split()[1] + ' cannot be parsed')

    output_sheet.write(line + '\n')

print()
print('====================================')
print('Parsed: %i' % parsed)
print('Unparseable: %i' % unparsed)
print('Found PMIDs: %i' % found)
print('Found NEW PMIDS: %i' % newpmids)
print('No new PMIDs: %i' % nopmids)
print('Had zero before T2G: %i' % hadzero)
print()
print('Pct of parseable variants annotated with new evidence: %d' % (100 * (float(newpmids) / float(parsed))))
print('Pct of parseable variants annotated by Text2Gene: %d' % (100 * (float(found) / float(parsed))))
print()
print('Number variants with zero evidence newly annotated by Text2Gene: %i' % hadzero)


