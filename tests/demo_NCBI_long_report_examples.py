from __future__ import absolute_import, print_function

from text2gene.api import LVGEnriched
from text2gene.ncbi import get_ncbi_variant_report

hgvs_problems = ['NM_000063.4:c.1360+62G>T', 'NM_001198945.1:c.603+8801G>A', 'NM_000059.3:c.1188T>G', 'NM_000059.3:c.7182A>G', 'NM_000059.3:c.1149C>A']

important_keys = ['Hgvs_c', 'Hgvs_g', 'Hgvs_p']

for hgvs_text in hgvs_problems:
    hgvs_extra_values = set()
    pmid_extra_values = set()
    found_hgvs_values_at = []
    report = get_ncbi_variant_report('NM_000063.4:c.1360+62G>T')
    rep_zero_values = [report[0]['Hgvs_c'], report[0]['Hgvs_g'], report[0]['Hgvs_p']]
    pmids = sorted(report[0]['PMIDs'])

    all_variant_strings = set(rep_zero_values)
    last_idx_of_unique_variant = 0

    for idx in range(len(report)):
        for key in important_keys:
            if report[idx][key] not in rep_zero_values:
                hgvs_extra_values.add(report[idx][key])
                found_hgvs_values_at.append(idx)
            if report[idx][key] not in all_variant_strings:
                all_variant_strings.add(report[idx][key])
                last_idx_of_unique_variant = idx

        for pmid in report[idx]['PMIDs']:
            if pmid not in pmids:
                pmid_extra_values.add(pmid)

    print()
    print('[%s] Report length: %i entries' % (hgvs_text, len(report)))
    print('[%s] Variants not in report[0]: %r' % (hgvs_text, hgvs_extra_values))
    print('[%s] Extra variants found in report indexes: %r' % (hgvs_text, found_hgvs_values_at))
    print('[%s] Extra PMIDs found after report[0]: %r' % (hgvs_text, pmid_extra_values))
    print('[%s] Last report containing unique variant: %i' % (hgvs_text, last_idx_of_unique_variant))
    print()
    print('LVGEnriched results for %s:' % hgvs_text)
    print(LVGEnriched(hgvs_text).variants)
    print()
    print()


