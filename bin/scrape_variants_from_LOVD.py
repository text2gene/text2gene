from __future__ import absolute_import, print_function, unicode_literals

import sys, re

import requests
import xmltodict

from IPython import embed

re_accession = re.compile('\/variants\/\w+\/(?P<acc_id>NM_\d+.\d+)\?')

LOVD_GENE_VARIANTS_URL = 'http://databases.lovd.nl/shared/api/rest.php/variants/%s'


class LOVDRemoteError(Exception):
    """ Raised when response from LOVD contains a not-ok status code.
    Error message should contain status code. 
    """
    pass


def parse_lovd_variants_by_gene_name_response(xml_blob, symbol):
    """ Parses LOVD response as provided by query_lovd_for_variants_by_gene_name

    :param xml_blob: (str) XML response from LOVD
    :param symbol: (str) gene name
    :return: dictionary of converted XML
    """
    variant_dicts = xmltodict.parse(xml_blob)['feed']['entry']
    out = []
    symbol = symbol.upper()

    for vari in variant_dicts:
        alt_link = (vari['link'][0]['@href'])
        accession_num = re_accession.findall(alt_link)[0]
        hgvs_text = vari['title'].replace(symbol, re_accession.findall(alt_link)[0])
        out.append(hgvs_text)

    return out


def query_lovd_for_variants_by_gene_name(symbol):
    """ Submits query to lovd.nl for specified gene name (Symbol).

    :param symbol: (str)
    :return: unparsed response content (str)
    :raises: LOVDRemoteError if not response.ok (message contains response.status_code)
    """

    response = requests.get(LOVD_GENE_VARIANTS_URL % symbol)
    if response.ok:
        return response.content
    else:
        raise LOVDRemoteError('lovd.nl returned HTTP %r' % response.status)

if __name__ == '__main__':
    try:
        symbol = sys.argv[1]
        api_response = query_lovd_for_variants_by_gene_name(symbol)
    except LOVDRemoteError as error:
        print(error)
        sys.exit()
    except IndexError:
        print('Supply gene Symbol name as argument to this script.  (e.g. ACVRL1)')
        sys.exit()


    print(parse_lovd_variants_by_gene_name_response(api_response, symbol))

    
