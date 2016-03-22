drop   table if exists hgvs_easymode;
create table           hgvs_easymode
select distinct
       Pathogenic.hgvs_text
from
	clinvar.hgvs_citations_pathogenic as Pathogenic,
	hgmd_pro.hgmd_hgvs HGMD
where
	HGMD.hgvs_text = Pathogenic.hgvs_text
order by
      HGMD.hgvs_text;

call create_index('hgvs_easymode', 'hgvs_text');  

