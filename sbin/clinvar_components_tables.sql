call log('components', 'begin');
-- ############################################

drop   table if exists variant_components; 
create table           variant_components select VariationID, variant_name, HGVS_p, HGVS_c, GeneID from variant_summary;

alter table variant_components add column Symbol varchar(25) default null;
alter table variant_components add column Ref varchar(10) default null;
alter table variant_components add column Pos smallint default null;
alter table variant_components add column Alt varchar(10) default null;
alter table variant_components add column PMID int(11) default null;

-- get the citation number out of the var_citations table
update variant_components VC, var_citations VarCit
    set VC.PMID = VarCit.citation_id 
    where VC.VariationID = VarCit.VariationID;

-- complete the Symbol column direcly from the Gene database
update clinvar.variant_components VC, gene.gene_info GDB
    set VC.Symbol = GDB.Symbol
    where VC.GeneID = GDB.GeneID;

-- Normalize!
update clinvar.variant_components set HGVS_p = NULL where HGVS_p = '-';
update clinvar.variant_components set HGVS_c = NULL where HGVS_c = '-';

-- Now we're ready to run the script that sets the Ref, Pos, and Alt columns.

call log('components', 'end');
