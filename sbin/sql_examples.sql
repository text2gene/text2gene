call create_index('m2p_SUB', 'PMID');
call create_index('m2p_SUB', 'SeqType');
call create_index('m2p_SUB', 'EditType');
call create_index('m2p_SUB', 'Pos');
call create_index('m2p_SUB', 'Ref');
call create_index('m2p_SUB', 'Alt');

-- example GeneID = 1837 (DTNA gene)

SELECT V.*
FROM
  gene2pubtator as G,
  m2p_SUB       as V
where
  G.PMID = V.PMID and
  G.GeneID = 1837;

-- example HGVS lookup in pubtator

select distinct M.* from gene2pubtator G, m2p_SUB M where G.PMID = M.PMID and G.GeneID = 120892 and pos=6055 and Ref = 'G' and Alt = 'A' and SeqType='c'; 


--
drop   table  if exists  gene2mutation2pubmed;
create table             gene2mutation2pubmed
        select distinct  G.GeneID, G.PMID, M.Components
                   from  gene2pubtator G, mutation2pubtator M
                   where G.PMID=M.PMID;

call create_index('gene2mutation2pubmed', 'Components');
call create_index('gene2mutation2pubmed', 'GeneID');
call create_index('gene2mutation2pubmed', 'PMID');
call create_index('gene2mutation2pubmed', 'GeneID,PMID');
call create_index('gene2mutation2pubmed', 'GeneID,Components');



