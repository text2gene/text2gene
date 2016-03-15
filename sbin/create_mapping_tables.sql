create table lvg_mappings (
     hgvs_text varchar(255) not null,
     hgvs_g varchar(255) default NULL,
     hgvs_c varchar(255) default NULL,
     hgvs_n varchar(255) default NULL,
     hgvs_p varchar(255) default NULL
);

call create_index("lvg_mappings", "hgvs_text,hgvs_g")
call create_index("lvg_mappings", "hgvs_text,hgvs_c")
call create_index("lvg_mappings", "hgvs_text,hgvs_n")
call create_index("lvg_mappings", "hgvs_text,hgvs_p")

create table ncbi_mappings (
     hgvs_text varchar(255) not null,
     hgvs_g varchar(255) default NULL,
     hgvs_c varchar(255) default NULL,
     hgvs_n varchar(255) default NULL,
     hgvs_p varchar(255) default NULL
);

call create_index("ncbi_mappings", "hgvs_text,hgvs_g")
call create_index("ncbi_mappings", "hgvs_text,hgvs_c")
call create_index("ncbi_mappings", "hgvs_text,hgvs_n")
call create_index("ncbi_mappings", "hgvs_text,hgvs_p")

create table pubtator_match (
     hgvs_text varchar(255) not null,
     PMID int(11) default NULL,
     ComponentString varchar(255) default NULL
);

call create_index("pubtator_match", "hgvs_text,PMID");

create table ncbi_match (
     hgvs_text varchar(255) not null,
     PMID int(11) default NULL
);

call create_index("ncbi_match", "hgvs_text,PMID");

create table clinvar_match (
     hgvs_text varchar(255) not null,
     PMID int(11) default NULL
);

call create_index("clinvar_match", "hgvs_text,PMID");

