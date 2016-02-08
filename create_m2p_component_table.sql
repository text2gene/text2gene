CREATE TABLE m2p_components (
  PMID int(10) unsigned DEFAULT NULL,
  Components varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
  Mentions text COLLATE utf8_unicode_ci NOT NULL,
  SeqType varchar(255) default NULL,
  EditType varchar(255) default NULL,
  Ref varchar(255) default NULL,
  Pos varchar(255) default NULL,
  Alt varchar(255) default NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci

call create_index('m2p_components','SeqType')
call create_index('m2p_components','EditType')
call create_index('m2p_components','Ref')
call create_index('m2p_components','Pos')
call create_index('m2p_components','Alt')

