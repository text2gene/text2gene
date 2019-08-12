call log('hgvs_citations', 'begin');

drop   table if exists hgvs_citations;
create table           hgvs_citations
select  DISTINCT
	H.VariationID, 
	H.HGVS,
	C.citation_id as PMID,
	S.ClinicalSignificance
from
	clinvar_hgvs  H,
	var_citations C,
	variant_summary S
where
	H.HGVS            like 'NM_%'     and 
	H.VariationID     = C.VariationID and
	C.VariationID     = S.VariationID and
	C.citation_source = 'PubMed'; 

call create_index('hgvs_citations', 'HGVS');
call create_index('hgvs_citations', 'VariationID');
call create_index('hgvs_citations', 'PMID'); 
call create_index('hgvs_citations', 'ClinicalSignificance');

drop   table if exists  hgvs_citations_pathogenic;
create table           hgvs_citations_pathogenic
select * from  hgvs_citations where ClinicalSignificance = 'Pathogenic';

drop   table if exists  hgvs_citations_benign;
create table           hgvs_citations_benign
select * from  hgvs_citations where ClinicalSignificance = 'Benign'; 

drop   table if exists  hgvs_citations_vus;
create table           hgvs_citations_vus
select * from  hgvs_citations where ClinicalSignificance = 'Uncertain significance';

drop   table if exists  hgvs_citations_conflict;
create table           hgvs_citations_conflict
select * from  hgvs_citations where
ClinicalSignificance = 'conflicting data from submitters'; 

call log('hgvs_citations', 'done');

