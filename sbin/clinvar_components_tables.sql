call log('components', 'begin');
-- ############################################

drop table if exists t2g_variant_summary; 
create table t2g_variant_summary select VariationID, variant_name, HGVS_p, HGVS_c, GeneID from variant_summary;

alter table t2g_variant_summary add column Symbol varchar(25) default null;
alter table t2g_variant_summary add column PMID int(11) default null;

-- get the citation number out of the var_citations table
call log('components', 'enriching PMID column from var_citations table');
update t2g_variant_summary VC, var_citations VarCit
    set VC.PMID = VarCit.citation_id 
    where VC.VariationID = VarCit.VariationID;

-- Remove entries that have no citation (what would be the point?)
call log('components', 'removing entries without citations');
delete from t2g_variant_summary where PMID is NULL;

-- complete the Symbol column direcly from the Gene database
call log('components', 'completing Symbol (gene name) column using Gene database');
update clinvar.t2g_variant_summary VC, gene.gene_info GDB
    set VC.Symbol = GDB.Symbol
    where VC.GeneID = GDB.GeneID;

-- Normalize!
call log('components', 'normalizing hgvs columns to NULL if set to "-"');
update clinvar.t2g_variant_summary set HGVS_p = NULL where HGVS_p = '-';
update clinvar.t2g_variant_summary set HGVS_c = NULL where HGVS_c = '-';

-- index on the fields we'll be searching on to build and check the t2g_hgvs_components table.
call log('components', 'indexing on VariationID and PMID and Symbol columns');
call create_index('t2g_variant_summary', 'VariationID');
call create_index('t2g_variant_summary', 'PMID');
call create_index('t2g_variant_summary', 'Symbol');

-- Create t2g_variant_summary table that will be filled by python script.
call log('components', 'creating t2g_hgvs_components table');
drop table if exists t2g_hgvs_components;
create table t2g_hgvs_components (
    id int(11) primary key auto_increment,
    VariationID int(11),
    hgvs_text varchar(255),
    PMID int(11) default null,
    GeneID int(11) default null,
    Symbol varchar(20) default null,
    Ref varchar(10) default null,
    Pos int(11) default null,
    Alt varchar(10) default null,
    EditType varchar(25) default null,
    SeqType varchar(10) default null
);

-- index on our most useful mutation component search fields and also our component combo.
call create_index('t2g_hgvs_components', 'hgvs_text');
call create_index('t2g_hgvs_components', 'PMID');
call create_index('t2g_hgvs_components', 'Symbol');
call create_index('t2g_hgvs_components', "Symbol,Pos,Ref");
call create_index('t2g_hgvs_components', "Symbol,Pos,Ref,Alt");

-- What have we now?
call info;

-- Now we're ready to run sbin/create_clinvar_components_table.py
call log('components', 'ready to run sbin/create_clinvar_components_table.py');
call log('components', 'end');

