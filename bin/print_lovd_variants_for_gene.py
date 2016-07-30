from __future__ import print_function, unicode_literals

import re
import sys

from lxml import etree
from lxml.html import HTMLParser

import requests

from metavariant.lovd import *
from metavariant.exceptions import *

re_pubmed_id = re.compile('pubmed\/(?P<pmid>\d+)')
re_doi = re.compile(r'(10[.][0-9]{2,}(?:[.][0-9]+)*/(?:(?!["&\'])\S)+)')


#LOVD_GENE_VARIANT_LIST_URL = 'http://databases.lovd.nl/shared/view/{gene}#page_size=1000&page=1'
LOVD_GENE_VARIANT_LIST_URL = 'http://databases.lovd.nl/shared/variants/{gene}/unique#object_id=VariantOnTranscriptUnique%2CVariantOnGenome&id={gene}&order=VariantOnTranscript%2FDNA%2CASC&skip[chromosome]=chromosome&skip[allele_]=allele_&skip[transcriptid]=transcriptid&skip[owner_countryid]=owner_countryid&page_size=1000&page=1'


def get_num_results(page_body, symbol):
    span = htm.cssselect('#viewlistPageSplitText_CustomVL_VIEW_%s' % symbol).text


def get_references_from_td(td_elem):
    refs = {'doi': [], 'pmid': []}
    for span in td_elem.findall('span'):
    
        if span.text.startswith('Journal'):
            #look for a DOI?
            stuff = span.get('onmouseover')
            doi = re_doi.findall(stuff)[0].strip('\\')
            if doi:
                refs['doi'].append(doi)
            
        if span.text.startswith('PubMed'):
            if span.text.startswith('PubMed'):
                stuff = span.get('onmouseover')
                pmid = re_pubmed_id.findall(stuff)[0]
                if pmid:
                    refs['pmid'].append(pmid)
    return refs


def get_vdict_from_tr(tr_elem):
    tds = tr_elem.getchildren()
    return {'allele': tds[6].text,
     'dbSNP': tds[13].text,
     'disease': tds[23].text,
     'dna': tds[2].find('a').text,
     'exon': tds[1].text,
     'effect': tds[0].text,
     'frequency': tds[16].text,
     'genomic':  tds[7].find('a').text,
     'haplotype': tds[5].text,
     'LOVD_id': tds[10].text,
     'protein': tds[4].text,
     'reference': get_references_from_td(tds[12]),
     'remarks': tds[25].text,
     'rna': tds[3].text
    }


try:
    symbol = sys.argv[1]
except IndexError:
    print()
    print('Supply gene symbol (e.g. "UGT1A1") as argument to this script.')
    print()
    sys.exit()


#url = 'http://databases.lovd.nl/shared/variants/{gene}/unique#object_id=VariantOnTranscriptUnique%2CVariantOnGenome&id={gene}&order=VariantOnTranscript%2FDNA%2CASC&page_size=1000&page=1'.format(gene=symbol)

#url = 'http://databases.lovd.nl/shared/view/%s' % symbol

url = LOVD_GENE_VARIANT_LIST_URL.format(gene=symbol)
print(url)

result_dict = {}

response = requests.get(url)

htm = etree.fromstring(response.content, parser=HTMLParser()).find('body')
try:
    table = htm.cssselect('#viewlistTable_CustomVL_VIEW_%s' % symbol)[0]
except:
    table = htm.cssselect('#viewlistTable_CustomVL_VOTunique_VOG_%s' % symbol)[0]

for tr in table.findall('tr'):
    print(get_vdict_from_tr(tr))


