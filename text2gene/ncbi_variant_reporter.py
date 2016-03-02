from __future__ import absolute_import, print_function, unicode_literals

import requests

from .exceptions import Text2GeneError

ncbi_result_keys = ['Submitted ID',
                     'Submitted Loc',
                     'Cytoband',
                     'Mapped Loc',
                     'NCBI ID',
                     'Allele',
                     'GMAF',
                     'Gene ID',
                     'Gene Symbol',
                     'Hgvs_g',
                     'Origin',
                     'Hgvs_g (RefSeqGene)',
                     'Hgvs_c',
                     'Hgvs_p',
                     'Consequences',
                     'OnTestPanel',
                     'ClinVar Accession',
                     'Clinical Source ID',
                     'Clinical Significance',
                     'Clinical Evidence',
                     'Clinical Review',
                     'Phenotype ID',
                     'Phenotype Description',
                     'PMIDs',
                     'Number Of Submissions',
                     'Suspected False Positive',
                     'GWAS Association',
                     'Has Genotype?',
                     'On Genotyping Kit?',
                     'Exception',
                     'Novel allele?',
                    ]


def ncbi_tsv_to_dict(tsv):
    """ Take NCBI Variant Reporter TSV results and return a dictionary containing
    one key-value pair per item in the result TSV.

    :param tsv: str
    :return: dict
    """
    outd = {}
    keystr, valuestr = tsv.strip('\n').split('\n')
    values = valuestr.split('\t')

    for idx in range(0, len(ncbi_result_keys)-1):
        outd[ncbi_result_keys[idx]] = values[idx]
    return outd


def ncbi_preamble_to_dict(preamble):
    """ Take NCBI Variant Reporter preamble for results and return a dictionary containing
    one key-value pair per item appearing as "## KEY: VALUE\n"

    :param preamble: str
    :return: dict
    """
    #TODO (possibly never, not sure if we need this)
    raise NotImplementedError


def process_ncbi_return(return_text):
    """ Break NCBI Variant Reporter response content into preamble and tsv. Turn TSV results
    into a dictionary of TSV results (via ncbi_tsv_to_dict function).

    :param return_text: str
    :return: tuple (preamble, results_dict) (str, dict)
    """
    preamble, tsv = return_text.split('\n\n# ')
    results_dict = ncbi_tsv_to_dict(tsv)
    return(preamble, results_dict)


def NCBI_Variant_Report(hgvs_text):
    """ Takes hgvs_text string and queries the NCBI Variant Report tool.

    :param hgvs_text: str
    :return: tuple (preamble, results_dict) (str, dict)
    """
    response = requests.get("http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi", params={'annot1': hgvs_text})
    if not response.ok:
        raise Text2GeneError('NCBI Variant Reporter failed lookup of %s (http %i)' % (hgvs_text, response.status_code))

    return process_ncbi_return(response.content)



if __name__ == '__main__':
    sample_ncbi_return = """
Submitted: JSID_01_827918_130.14.22.21_9000__variant_analyzer
.
## URL: http://www.ncbi.nlm.nih.gov/variation/tools/reporter/JSID_01_827918_130.14.22.21_9000__variant_analyzer
## Submitted time:	03/01/2016 16:50:35
## Report generated time:	03/01/2016 16:50:36
## Summary report for
## Summary of Submitted Data
## Number of variant locations:	1
## Number of variant alleles:	1
## Summary of Data Report:
## Number of unique NCBI Ids found:	1
## Number of novel alleles at known locations:	0
## Number of novel alleles at novel locations:	0
## Total number of novel locations:	0
## Variant alleles with clinical information:	1
## Variant alleles with molecular consequence:	1
## Total number of rows in the report:	1
## Assembly:	GRCh37.p13

# Submitted ID	Submitted Loc	Cytoband	Mapped Loc	NCBI ID	Allele	GMAF	Gene ID	Gene Symbol	Hgvs_g	Origin	Hgvs_g (RefSeqGene)	Hgvs_c	Hgvs_p	Consequences	OnTestPanel	ClinVar Accession	Clinical Source ID	Clinical Significance	Clinical Evidence	Clinical Review	Phenotype ID	Phenotype Description	PMIDs	Number Of Submissions	Suspected False Positive	GWAS Association	Has Genotype?	On Genotyping Kit?	Exception	Novel allele?
NM_014855.2:c.333G>C	NM_014855.2: 418	7p22	NM_014855.2:418	rs11549840	NC_000007.13:g.4821352G>C	C: 0.0126	9907	AP5Z1	NC_000007.13:g.4821352G>C	germline	NG_028111.1:g.11091G>C	NM_014855.2:c.333G>C	NP_055670.1:p.Gln111His	SO:0001583 (non_synonymous_codon)		RCV000116378.2		Likely benign	clinical testing	no_criteria	MedGen:CN169374	not specified		17				Yes
"""

    preamble, tsv = sample_ncbi_return.split('\n\n')
    print('PREAMBLE:')
    print(preamble)
    print()
    print('TSV as Dictionary:')
    print(ncbi_tsv_to_dict(tsv))
