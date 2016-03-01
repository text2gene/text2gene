from __future__ import absolute_import, print_function, unicode_literals

import hgvs.dataproviders.uta as uta
import hgvs.parser
import hgvs.variantmapper
from hgvs.exceptions import HGVSDataNotAvailableError


from .hgvs_components import HgvsComponents

hgvs_parser = hgvs.parser.Parser()

uta = hgvs.dataproviders.uta.connect()
mapper = hgvs.variantmapper.EasyVariantMapper(uta)


def _seqvar_map_func(in_type, out_type):
    func_name = '%s_to_%s' % (in_type, out_type)
    return getattr(mapper, func_name)


def variant_to_gene_name(seqvar):
    """
    Get HUGO Gene Name (Symbol) for given sequence variant object.

    Input seqvar must be of type 'n', 'c', or 'p'.

    :param variant: hgvs.SequenceVariant
    :return: string gene name (or None if not available).
    """
    if seqvar.type in ['n', 'c', 'p']:
        try:
            tx_identity = uta.get_tx_identity_info(seqvar.ac)
        except HGVSDataNotAvailableError:
            return None

        if tx_identity is not None:
            return tx_identity[-1]
        else:
            return None
    else:
        return None

        
class HgvsLVG(object):

    def __init__(self, hgvs_text, **kwargs):
        self.hgvs_text = hgvs_text

        # use the hgvs library to get us some info about this HGVS string.
        self.seqvar = self.parse(hgvs_text)

        # initialize transcripts list
        self.transcripts = set(kwargs.get('transcripts', []))

        # fill in all the different ways to talk about this variant in each sequence type.
        self.variants = {'g': set(), 'c': set(), 'n': set(), 'p': set()}
        self.variants[self.seqvar.type].add(self.seqvar)

        if self.seqvar.type == 'p':
            # no backreference to 'c','g','n' possible from a 'p' seqvar
            self.variants['p'] = [self.seqvar]

        if self.variants['c']:
            # attempt to derive all 4 types of SequenceVariants from 'c'.
            for this_type, value in list(self.variants.items()):
                if this_type != 'c':
                    self.variants[this_type].add(_seqvar_map_func(self.seqvar.type, this_type)(self.seqvar))

        if self.variants['g']:
            for var_g in self.variants['g']:
                for trans in self.get_transcripts(var_g):
                    self.transcripts.add(trans)

        if self.seqvar.type == 'g' and self.transcripts:
            # we still need to collect 'c', 'p', and 'n' variants
            for trans in self.transcripts:
                self.variants['c'].add(mapper.g_to_c(self.seqvar, trans))
                self.variants['n'].add(mapper.g_to_n(self.seqvar, trans))

            for seqvar in self.variants['c']:
                self.variants['p'].add(mapper.c_to_p(seqvar))

        # if we get transcripts, we can do g_to_c and g_to_n
        if self.transcripts:
            for trans in self.transcripts:
                for var_g in self.variants['g']:
                    self.variants['c'].add(mapper.g_to_c(var_g, trans))
                    self.variants['n'].add(mapper.g_to_n(var_g, trans))

        # find out the gene name of this variant.
        self._gene_name = None

    @property
    def gene_name(self):
        if self._gene_name is None:     # and self.seqvar.type != 'p':
            if self.variants['c']:
                chosen_one = list(self.variants['c'])[0]
            elif self.variants['n']:
                chosen_one = list(self.variants['n'])[0]
            else:
                chosen_one = list(self.variants['p'])[0]
            self._gene_name = variant_to_gene_name(chosen_one)
        return self._gene_name

    @staticmethod
    def get_transcripts(var_g):
        return mapper.relevant_transcripts(var_g)

    @staticmethod
    def parse(hgvs_text):
        return hgvs_parser.parse_hgvs_variant(hgvs_text)

    def to_dict(self, with_gene_name=True):
        """Returns contents of object as a 2-level dictionary.

        Supply with_gene_name = True [default: True] to return gene_name as well.

        (gene_name is a lazy-loaded magic attribute, and may take a second or two).
        """
        outd = self.__dict__

        if with_gene_name:
            outd['gene_name'] = self.gene_name

        outd.pop('_gene_name')

        # turn sets into lists
        outd['transcripts'] = list(self.transcripts)
        for seqtype, seqvars in (self.variants.items()):
            outd['variants'][seqtype] = list(seqvars)
        return outd

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

    print(hgvs_obj)

    print()
    print(HgvsComponents(hgvs_obj.seqvar))
    print()

    for vartype in list(hgvs_obj.variants.keys()):
        print(hgvs_obj.variants[vartype])

    print()
    print(hgvs_obj.gene_name)
