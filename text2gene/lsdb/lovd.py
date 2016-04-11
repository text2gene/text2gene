from __future__ import absolute_import, unicode_literals

LOVD_LISTS = {'dmd.nl': {'url': 'http://www.dmd.nl/nmdb2/variants.php?select_db={gene}&action=search_unique&search_Variant%2FDNA=c.{pos}',
                         'genes': ['ACTA1', 'ANKRD1', 'ANO5', 'B3GNT1', 'BAG3', 'BANF1',
                                   'BIN1', 'CAPN3', 'CAV3', 'CCDC78', 'CCT5', 'CFL2',
                                   'CHAT', 'CHKB', 'CHRNA1', 'CHRNB1', 'CHRND', 'CHRNE',
                                   'CNTN1', 'COL6A1', 'COL6A2', 'COL6A3', 'COLQ', 'CRYAB',
                                    'DAG1', 'DES', 'DMD', 'DMD_d', 'DNAJB6', 'DOK7', 'DPM3',
                                    'DTNA', 'DYSF', 'EGR2', 'EMD', 'FAM134B', 'FGD4', 'FHL1',
                                    'FIG4', 'FKRP', 'FKTN', 'GARS', 'GDAP1', 'GFPT1', 'GJB1',
                                    'GK', 'IGHMBP2', 'IKBKAP', 'ISCU', 'ITGA7', 'KBTBD13',
                                    'KIF1B', 'KLHL40', 'LAMA2', 'LAMP2', 'LARGE', 'LDB3',
                                    'LITAF', 'LMNA', 'MATR3', 'MFN2', 'MICU1', 'MPZ', 'MSTN',
                                    'MTM1', 'MTMR14', 'MTMR2', 'MUSK', 'MYBPC3', 'MYH7', 'MYL2',
                                    'MYL3', 'MYOT', 'MYOZ1', 'MYOZ2', 'MYOZ3', 'MYPN', 'NDRG1',
                                    'NEB', 'NEFL', 'NGF', 'NTRK1', 'PABPN1', 'PDK3', 'PDLIM3',
                                    'PLEC', 'PLEKHG5', 'PMP22', 'POMGNT1', 'POMT1', 'POMT2',
                                    'PRPS1', 'PRX', 'PTRF', 'RAB7A', 'RAPSN', 'RYR1', 'SBF2',
                                    'SEPN1', 'SEPT9', 'SETX', 'SGCA', 'SGCB', 'SGCD', 'SGCE',
                                    'SGCG', 'SGCZ', 'SH3TC2', 'SMN1', 'SOX10', 'SPTLC1', 'SPTLC2',
                                    'SSPN', 'SYNE1', 'SYNE2', 'TCAP', 'TNNI2', 'TNNI3', 'TNNT1',
                                    'TNNT2', 'TNNT3', 'TNPO3', 'TPM1', 'TPM2', 'TPM3', 'TRAPPC11',
                                    'TRDN', 'TRIM32', 'TTR', 'VCP', 'VMA21', 'WNK1', 'YARS',
                                    'ZMPSTE24'],
                          },

              'chromium.lovd.nl': {'url': 'http://chromium.lovd.nl/LOVD2/variants.php?select_db={gene}&action=search_unique&search_Variant%2FDNA=c.{pos}',
                                   'genes': ['ABCA13', 'ARG1', 'ASL', 'ASS1',
                                             'ATM', 'ATP1A2', 'CACNA1A', 'CACNA1S',
                                             'CDKN2A', 'CLCN1', 'CPS1', 'CREBBP',
                                             'ESCO2', 'GAA', 'GLRA1', 'HGSNAT',
                                             'LRP5', 'NOTCH3', 'NR0B1', 'NSD1', 'OTC',
                                             'RNF135', 'SAMHD1', 'SCN4A', 'SLC25A13',
                                             'SLC25A15', 'SOST', 'TCF4', 'TREX1']
                                   }
}

LOVD_NL_URL = 'http://databases.lovd.nl/shared/variants/{gene}/unique#object_id=VariantOnTranscriptUnique%2CVariantOnGenome&id={gene}&search_VariantOnTranscript/DNA=c.{pos}'

def get_lovd_url(gene_name, position):
    for host in LOVD_LISTS.keys():
        if gene_name in LOVD_LISTS[host]['genes']:
            return LOVD_LISTS[host]['url'].format(gene=gene_name, pos=position)
        else:
            return LOVD_NL_URL.format(gene=gene_name, pos=position)


def extract_gene_names_from_LOVD_html(options_list_html):
    gene_names = []
    opts = options_list_html.split('\n')
    for opt in opts:
        gene = opt.split('value="')[1].split('"')[0]
        gene_names.append(gene)

    return gene_names
