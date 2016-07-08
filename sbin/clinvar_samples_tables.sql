call log('samples', 'begin');
-- ############################################

drop   table if exists var_citations_count; 
create table           var_citations_count select VariationID, count(*) num_citations from var_citations group by VariationID ;

call utf8_unicode('molecular_consequences');

call create_index('var_citations_count', 'VariationID');

-- ############################################

drop   table if exists samples;
create table           samples like  clinvar.clinvar_hgvs;

alter table samples drop column AlleleID;
alter table samples drop column RCVaccession; 

alter table samples add column Symbol varchar(20) ; 
alter table samples add column Consequence varchar(100);
alter table samples add column SequenceOntologyID varchar(20);
alter table samples add column num_citations smallint;
alter table samples add column ClinicalSignificance varchar(200);
alter table samples add column hgmd_acc_num  varchar(10);

insert into samples (VariationID, hgvs_text)
select      distinct VariationID, hgvs_text from clinvar_hgvs where hgvs_text like 'NM_%c.%'; 

call create_index('samples', 'VariationID');
call create_index('samples', 'hgvs_text');

-- ############################################

update samples CV,
       variant_summary S
set    CV.ClinicalSignificance = S.ClinicalSignificance,
       CV.Symbol = S.Symbol
where  CV.VariationID   = S.VariationID;

update samples CV,
       molecular_consequences M 
set    CV.SequenceOntologyID = M.SequenceOntologyID, 
       CV.Consequence = M.Value
where  CV.hgvs_text = M.hgvs_text ;

update samples CV,
       var_citations_count P
set    CV.num_citations = P.num_citations
where  CV.VariationID   = P.VariationID;

-- update samples CV,
--        hgmd_pro.hgmd_hgvs HGMD
-- set    CV.hgmd_acc_num = HGMD.acc_num
-- where  CV.hgvs_text = HGMD.hgvs_text ;

call create_index('samples', 'Consequence');
call create_index('samples', 'Symbol');
call create_index('samples', 'ClinicalSignificance');
call create_index('samples', 'Consequence, ClinicalSignificance');
call create_index('samples', 'num_citations');
call create_index('samples', 'hgmd_acc_num');

-- ############################################

-- mysql> call freq('samples', 'Consequence') ; 
-- +--------------------------------------------------------------------------------------+
-- | @sql_cnt                                                                             |
-- +--------------------------------------------------------------------------------------+
-- | select Consequence,count(*) as cnt from samples group by Consequence order by cnt desc           
-- +--------------------------------------------------------------------------------------+

-- drop   table if exists samples_hgmd;
-- create table           samples_hgmd like samples;
-- insert into            samples_hgmd select * from  samples where hgmd_acc_num is not null;

drop   table if exists samples_vus;
create table           samples_vus like samples;
insert into            samples_vus select * from  samples where ClinicalSignificance = 'Uncertain significance'; 

drop   table if exists samples_pathogenic;
create table           samples_pathogenic like samples;
insert into            samples_pathogenic select * from  samples where ClinicalSignificance = 'Pathogenic'; 

drop   table if exists samples_nonsense;
create table           samples_nonsense like samples;
insert into            samples_nonsense select * from  samples where Consequence = 'STOP-GAIN';

drop   table if exists samples_nonsense_pathogenic;
create table           samples_nonsense_pathogenic like samples;
insert into            samples_nonsense_pathogenic select * from  samples_nonsense where ClinicalSignificance = 'Pathogenic';

-- drop   table if exists samples_nonsense_pathogenic_hgmd;
-- create table           samples_nonsense_pathogenic_hgmd like samples;
-- insert into            samples_nonsense_pathogenic_hgmd select * from  samples_nonsense_pathogenic where hgmd_acc_num is not null;

drop   table if exists samples_frameshift;
create table           samples_frameshift like samples;
insert into            samples_frameshift select * from  samples where Consequence = 'frameshift';

drop   table if exists samples_missense;
create table           samples_missense like samples;
insert into            samples_missense select * from  samples where Consequence = 'missense';

drop   table if exists samples_missense_vus;
create table           samples_missense_vus like samples;
insert into            samples_missense_vus select * from  samples_missense where ClinicalSignificance = 'Uncertain significance';

drop   table if exists samples_silent;
create table           samples_silent like samples;
insert into            samples_silent select * from  samples where Consequence = 'cds-synon';

drop   table if exists samples_silent_vus;
create table           samples_silent_vus like samples;
insert into            samples_silent_vus select * from  samples_silent where ClinicalSignificance = 'Uncertain significance';

drop   table if exists samples_intron;
create table           samples_intron like samples;
insert into            samples_intron select * from  samples where Consequence = 'intron';

drop   table if exists samples_intron_vus;
create table           samples_intron_vus like samples;
insert into            samples_intron_vus select * from  samples_intron where ClinicalSignificance = 'Uncertain significance';

drop   table if exists samples_gene_dmd;
create table           samples_gene_dmd like samples;
insert into            samples_gene_dmd select * from  samples where Symbol = 'DMD'; 

call log('samples', 'done'); 
