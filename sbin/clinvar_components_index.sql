-- index on our most useful mutation component search fields and also our component combo.
call create_index('t2g_hgvs_components', 'hgvs_text');
call create_index('t2g_hgvs_components', 'PMID');
call create_index('t2g_hgvs_components', 'Symbol');
call create_index('t2g_hgvs_components', "Symbol,Pos,Ref");
call create_index('t2g_hgvs_components', "Symbol,Pos,Ref,Alt");

