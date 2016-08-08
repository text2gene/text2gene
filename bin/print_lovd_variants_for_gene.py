from __future__ import print_function, unicode_literals

import re
import sys

from lxml import etree
from lxml.html import HTMLParser

import requests

from metavariant.lovd import LOVDAnnotatedVariants

re_pubmed_id = re.compile('pubmed\/(?P<pmid>\d+)')
re_doi = re.compile(r'(10[.][0-9]{2,}(?:[.][0-9]+)*/(?:(?!["&\'])\S)+)')


LOVD_GENE_VARIANT_LIST_URL = 'http://databases.lovd.nl/shared/view/{gene}#page_size=1000&page=1'
#LOVD_GENE_VARIANT_LIST_URL = 'http://databases.lovd.nl/shared/variants/{gene}/unique#object_id=VariantOnTranscriptUnique%2CVariantOnGenome&id={gene}&order=VariantOnTranscript%2FDNA%2CASC&skip[chromosome]=chromosome&skip[allele_]=allele_&skip[transcriptid]=transcriptid&skip[owner_countryid]=owner_countryid&page_size=1000&page=1'


def get_num_results(page_body, symbol):
    span = htm.cssselect('#viewlistPageSplitText_CustomVL_VIEW_%s' % symbol).text


try:
    symbol = sys.argv[1]
except IndexError:
    print()
    print('Supply gene symbol (e.g. "UGT1A1") as argument to this script.')
    print()
    sys.exit()


for lovd_var in LOVDAnnotatedVariants(symbol, 'chromium.lovd.nl'):
    print(lovd_var.hgvs_text)
    print(lovd_var.references)

print(lovd_var.to_dict())

