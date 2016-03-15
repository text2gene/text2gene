create table lvg_mappings (
     hgvs_text varchar(255) primary key not null,
     hgvs_g varchar(255) default NULL,
     hgvs_c varchar(255) default NULL,
     hgvs_n varchar(255) default NULL,
     hgvs_p varchar(255) default NULL
);

create table ncbi_mappings (
     hgvs_text varchar(255) primary key not null,
     hgvs_g varchar(255) default NULL,
     hgvs_c varchar(255) default NULL,
     hgvs_n varchar(255) default NULL,
     hgvs_p varchar(255) default NULL
);

create table pubtator_match (
     hgvs_text varchar(255) primary key not null,
     PMID int(11) default NULL,
     ComponentString varchar(255) default NULL
);

call create_index("pubtator_match", "hgvs_text,PMID");

create table ncbi_match (
     hgvs_text varchar(255) primary key not null,
     PMID int(11) default NULL
);

call create_index("ncbi_match", "hgvs_text,PMID");

create table clinvar_match (
     hgvs_text varchar(255) primary key not null,
     PMID int(11) default NULL
);

call create_index("clinvar_match", "hgvs_text,PMID");

