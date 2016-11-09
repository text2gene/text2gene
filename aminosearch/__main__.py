from .sqldata import SQLData

db = SQLData()

import hgvs
import hgvs.parser
import hgvs.dataproviders.uta as uta

if __name__=='__main__':
    hdp = uta.connect()
    hp = hgvs.parser.Parser()
    input = 'NC_000001.10:g.216219781A>G'
    hp.parse_hgvs_variant(input)
    var_g = hp.parse_hgvs_variant(input)
    print(var_g)

