from __future__ import absolute_import, unicode_literals

from medgen.api import ClinvarVariationID

def hgvs_to_clinvar_variationID(hgvs_text):
    var_ids = ClinvarVariationID(hgvs_text)
    return var_ids[0]

def get_variation_url(varID):
    return 'http://www.ncbi.nlm.nih.gov/clinvar/variation/{}'.format(varID)

def get_pubmed_url(pmid):
    return 'http://www.ncbi.nlm.nih.gov/pubmed/{}'.format(pmid)

def get_pubtator_url(pmid):
    url_tmpl = 'http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/curator_identifier.cgi?user=User63310122&pmid={pmid}&searchtype=PubMed_Search&query={pmid}&page=1&Species_display=1&Chemical_display=1&Gene_display=1&Disease_display=1&Mutation_display=1&tax='
    return url_tmpl.format(pmid=pmid)

def get_lovd_url(gene_name, position):
    if gene_name == "DMD":
        tmpl = 'http://www.dmd.nl/nmdb2/variants.php?select_db=DMD&action=search_unique&search_Variant%2FDNA={pos}'
    elif gene_name == 'MLH1':
        tmpl = 'http://chromium.lovd.nl/LOVD2/colon_cancer/variants.php?select_db=MLH1&action=search_unique&order=Variant%2FDNA%2CASC&search_Variant%2FDNA={pos}'
    elif gene_name == 'OTOF':
        tmpl = 'https://research.cchmc.org/LOVD2/variants.php?select_db=OTOF&action=search_unique&order=Variant%2FDNA%2CASC&search_Variant%2FDNA={pos}'
    else:
        return 'NOPE'
    return tmpl.format(pos=position)

def get_hgnc_url_for_hgnc_id(gene_id):
    return 'http://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=HGNC:{}'.format(gene_id)

def get_hgnc_url_for_gene_name(gene_name):
    return 'http://www.genenames.org/cgi-bin/search?search_type=all&search={}&submit=Submit'.format(gene_name)