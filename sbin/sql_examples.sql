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

