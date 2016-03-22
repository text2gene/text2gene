from text2gene.training import Experiment

experiment = Experiment('clinvar_pathogenic',
                        hgvs_examples_table = 'hgvs_citations_pathogenic',
                        hgvs_examples_db = 'clinvar',
                        lvg_mode = 'ncbi_enriched')

experiment.run()

