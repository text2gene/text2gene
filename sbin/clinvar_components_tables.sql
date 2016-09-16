call log('components', 'begin');
-- ############################################

drop   table if exists variant_components; 
create table           variant_components select VariationID, variant_name, HGVS_p, HGVS_c, GeneID from variant_summary;

alter table variant_components add column id int(11) primary key auto_increment;
alter table variant_components add column Symbol varchar(25) default null;
alter table variant_components add column Ref varchar(10) default null;
alter table variant_components add column Pos smallint default null;
alter table variant_components add column Alt varchar(10) default null;
alter table variant_components add column PMID int(11) default null;
alter table variant_components add column EditType varchar(25) default null;
alter table variant_components add column SeqType varchar(10) default null;

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

-- Remove entries that have no citation (what would be the point?)
call log('components', 'removing entries without citations');
delete from variant_components where PMID is NULL;

-- index on our most useful search fields
call create_index('variant_components', 'VariationID');
call create_index('variant_components', 'PMID');
call create_index('variant_components', 'Symbol');

-- What have we now?
call info;

-- Now we're ready to run the script that sets the Ref, Pos, and Alt columns.

call log('components', 'end');
