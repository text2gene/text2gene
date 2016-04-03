from __future__ import absolute_import, unicode_literals

from medgen.api import ClinvarVariationID, ClinVarDB
from medgen.api import GeneID, GeneName


class GeneInfo(object):

    def __init__(self, gene_id=None, gene_name=None):
        if gene_id:
            self.gene_id = gene_id
            self.gene_name = GeneName(gene_id)
        elif gene_name:
            self.gene_name = gene_name
            self.gene_id = GeneID(gene_name)

    @property
    def ncbi_url(self):
        return 'http://www.ncbi.nlm.nih.gov/gene/{gene_id}'.format(gene_id=self.gene_id)

    @property
    def medgen_url(self):
        return 'http://www.ncbi.nlm.nih.gov/medgen?term={gene_name}%5BGene%5D'.format(gene_name=self.gene_name)

    @property
    def gtr_url(self):
        return 'http://www.ncbi.nlm.nih.gov/gtr/genes/{gene_id}'.format(gene_id=self.gene_id)

    @property
    def hgnc_url(self):
        return 'http://www.genenames.org/cgi-bin/search?search_type=all&search={}&submit=Submit'.format(self.gene_name)

    @property
    def gtr_pubmeds_url(self):
        return 'http://www.ncbi.nlm.nih.gov/pubmed/?LinkName=gene_pubmed&from_uid={gene_id}'.format(gene_id=self.gene_id)


def hgvs_to_clinvar_variationID(hgvs_text):
    var_ids = ClinvarVariationID(hgvs_text)
    if len(var_ids) > 0:
        return var_ids[0]
    else:
        return None

def get_variation_url(varID):
    return 'http://www.ncbi.nlm.nih.gov/clinvar/variation/{var_id}'.format(var_id=varID)

def get_pubmed_url(pmid):
    return 'http://www.ncbi.nlm.nih.gov/pubmed/{pmid}'.format(pmid=pmid)

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
        return None
    return tmpl.format(pos=position)


def get_clinvar_tables_containing_variant(hgvs_text):
    """ Return list of hgvs sample tables that contain this hgvs_text. """

    db = ClinVarDB()
    out = []
    tname_pattern = 'samples%'

    sql = "select TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA = DATABASE() and TABLE_NAME LIKE '{}'".format(tname_pattern)
    results = db.fetchall(sql)

    tables = []
    for row in results:
        tables.append(row['TABLE_NAME'])

    sql_tmpl = 'select * from {tname} where hgvs_text = "{hgvs_text}"'
    for tname in tables:
        if db.fetchall(sql_tmpl.format(tname=tname, hgvs_text=hgvs_text)):
            out.append(tname)

    return out
