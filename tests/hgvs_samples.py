
supported_edittypes = ['SUB', 'DEL', 'FS', 'INDEL', 'DUP', 'INS']

hgvs_c = {'SUB': 'NM_198056.2:c.4786T>A',       # SCN5A
          'DEL': 'NM_007294.3:c.4964_4982delCTGGCCTGACCCCAGAAGA',       # BRCA1 / NP_009225.1:p.Ser1655TyrfsTer
          'FS': 'NM_000548.3:c.826_827del',     # 
          'INDEL': 'NM_000070.2:c.883_886delinsCTT',
          'DUP': 'NM_213599.2:c.191dup',
          'INS': 'NM_000256.3:c.3624_3625insC',     # MYBPC3 / NP_000247.2:p.Lys1209GlnfsTer
          'intron_SUB': 'NM_001267623.1:c.67-789C>A',
          'intron_SUB_plus': 'NM_033453.3:c.124+21A>C',
          
        }
          
hgvs_g = {'SUB': 'NC_000019.9:g.1399792C>T',        # GAMT / unknown protein effects
          'DEL': 'NC_000023.10:g.32841489delT',
          'FS': '',
          'INDEL': 'NC_000009.11:g.135147145_135147147delCAAinsAT', # SETX / NM_015046.5:c.7149_7151delinsAT / NM_015046.5:c.7149_7151delTTGinsAT
          'DUP': 'NC_000003.11:g.15685815dupT',     # SCN1A / NP_008851.3:p.Leu331PhefsTer
          'INS': '',
        }
          
hgvs_p = {'SUB': '',
          'DEL': 'NP_009225.1:p.Glu1000_Glu1001del', # BRCA1 / NM_007300.3:n.3230_3235delGAGGAA
          'FS': 'NP_009225.1:p.Ser1655TyrfsTer',    # BRCA1 / NM_007294.3:c.4964_4982delCTGGCCTGACCCCAGAAGA
          'INDEL': 'NP_000116.2:p.Cys447Ala',       # ESR1 / NM_001122742.1:c.1339_1340delTGinsGC
          'DUP': '',
          'INS': '',
        }
          
hgvs_n = {'SUB': 'NM_138924.2:n.421G>A',        # GAMT / unknown protein effects
          'DEL': 'NM_007300.3:n.3230_3235delGAGGAA',    # BRCA1 / NP_009225.1:p.Glu1000_Glu1001del
          'FS': '',
          'INDEL': '',
          'DUP': 'NM_001202435.1:n.1219dupT',   # SCN1A / NP_008851.3:p.Leu331PhefsTer
          'INS': '',
        }

