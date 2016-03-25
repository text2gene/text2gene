from __future__ import print_function, absolute_import, unicode_literals

import logging
log = logging.getLogger('hgvs_lexicon')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)

from hgvs.exceptions import *
from text2gene.ncbi import NCBIEnrichedLVG
from text2gene import LVGEnriched, PubtatorHgvs2Pmid

weird_list = open('RESULTS_pmids_not_found_in_ncbi_enriched_for_clinvar_examples.txt').readlines()

hgvs_weird = set()
for item in weird_list:
    hgvs_weird.add(item.split('\t')[0].strip())
 
hgvs_no_data = []
hgvs_other_error = []
fine = []
unicode_errors = []
text2gene_errors = []
ncbi_runtime_errors = []
pubtator_failures = []

for hgvs_text in hgvs_weird:
    try:
        lex = LVGEnriched(hgvs_text)
        fine.append(hgvs_text)
        print(hgvs_text, "fine")

        try:
            print('PubTator results:', PubtatorHgvs2Pmid(lex))
        except Exception as error:
            print('PubTator failed:', error)
            pubtator_failures.append(hgvs_text)

    except UnicodeEncodeError:
        unicode_errors.append(hgvs_text)
        print(hgvs_text, "unicode error")
    except HGVSDataNotAvailableError as error:
        hgvs_no_data.append(hgvs_text)
        print(hgvs_text, '%r' % error)
    except (HGVSInvalidIntervalError, HGVSParseError) as error:
        hgvs_other_error.append(hgvs_text)
        print(hgvs_text, '%r' % error)
    except IndexError as error:
        text2gene_errors.append(hgvs_text)
        print(hgvs_text, '%r' % error)        
    except RuntimeError as error:
        ncbi_runtime_errors.append(hgvs_text)
        print(hgvs_text, '%r' % error)
        
print('Totally Fine', len(fine))
print('HGVS NO DATA', len(hgvs_no_data))
print('HGVS Other Error', len(hgvs_other_error))
print('Unicode Error', len(unicode_errors))
print('Text2Gene error', len(text2gene_errors))
print('Pubtator failures', len(pubtator_failures))

from IPython import embed; embed()
