from __future__ import print_function, absolute_import, unicode_literals

import logging
log = logging.getLogger('hgvs.lvg')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)

from hgvs.exceptions import *
from text2gene.ncbi import NCBIEnrichedLVG
from text2gene import LVGEnriched

weird_list = open('RESULTS_pmids_not_found_in_ncbi_enriched_for_clinvar_examples.txt').readlines()

hgvs_weird = set()
for item in weird_list:
    hgvs_weird.add(item.strip())
 
hgvs_no_data = []
hgvs_other_error = []
fine = []
unicode_errors = []
text2gene_errors = []
ncbi_runtime_errors = []

for hgvs_text in hgvs_weird:
    try:
        lex = LVGEnriched(hgvs_text)
        fine.append(hgvs_text)
        print(hgvs_text, "fine")
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
        
print(len(hgvs_no_data))
print(len(hgvs_other_error))
print(len(fine))
print(len(unicode_errors))
print(len(text2gene_errors))

from IPython import embed; embed()