from __future__ import absolute_import, print_function

import hgvs.dataproviders.uta as uta
import hgvs.parser
import hgvs.variantmapper

hgvs_parser = hgvs.parser.Parser()

class HgvsLVG(object):

    def __init__(self, hgvs_text):
        self.hgvs_text = hgvs_text

        #self.c, self.r, self.p, self.g = self.parse(hgvs_text)
        self.seqvar = self.parse(hgvs_text)

    @staticmethod
    def parse(hgvs_text):
        return hgvs_parser.parse_hgvs_variant(hgvs_text)

    def __str__(self):
        out = 'HGVS input: %s\n' % self.hgvs_text
        out += '%r' % self.seqvar
        return out


if __name__=='__main__':
    import sys
    try:
        hgvs_text = sys.argv[1]
    except IndexError:
        print('Supply hgvs text as argument to this script.')
        sys.exit()

    hgvs_obj = HgvsLVG(hgvs_text) 

    #PubTatorSearch(hgvs_obj)

    print(hgvs_obj)

