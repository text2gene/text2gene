from __future__ import absolute_import, print_function, unicode_literals

import hgvs.dataproviders.uta as uta
import hgvs.parser
import hgvs.variantmapper

from .exceptions import RejectedSeqVar

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
        tx_identity = uta.get_tx_identity_info(seqvar.ac)
        if tx_identity is not None:
            return tx_identity[-1]
        else:
            return None
    else:
        return None


class HgvsComponents(object):

    """
    Special handling when SeqType comes in empty:
        If SeqType is none and REF in [a,c,t,g] and ALT in [a,c,t,g] --> then DNA or RNA 
        If SeqType is none and REF in [u] or ALT in [u] --> then DNA or RNA 
        If SeqType is none and REF in [AminoAcidsList] and ALT in [AminoAcidsList] --> then Protein
    """

    def __init__(self, seqvar=None, **kwargs):
        if seqvar:
            self.seqtype, self.edittype, self.ref, self.pos, self.alt = self.parse(seqvar)
        else:
            self.seqtype = kwargs.get('seqtype', None)
            self.edittype = kwargs.get('edittype', None)
            self.ref = kwargs.get('ref', None)
            self.pos = kwargs.get('pos', None)
            self.alt = kwargs.get('alt', None)

    @staticmethod
    def parse(seqvar):
        """ return tuple of sequence variant components as 
        (seqtype, edittype, ref, pos, alt)
        """
        if seqvar.type.strip() == '':
            print('Warning: SequenceVariant has empty seqtype. (%r)' % seqvar)
            seqtype = 'c'
        else:
            seqtype = seqvar.type

        ref = alt = edittype = pos = None

        try:
            ref = seqvar.posedit.edit.ref
            alt = seqvar.posedit.edit.alt
            edittype = seqvar.posedit.edit.type.upper()
        except AttributeError:
            # seqvar has incomplete edit information. fail out.
            print('Warning: SequenceVariant %s edit information incomplete or invalid.' % seqvar.ac)

        if seqtype == 'p':
            try:
                pos = '%s' % seqvar.posedit.pos.start.pos
                ref = '%s' % seqvar.posedit.pos.start.aa
            except AttributeError:
                raise RejectedSeqVar('Protein entry incomplete (unusable).')

        else:
            if seqvar.posedit.pos.end != seqvar.posedit.pos.start:
                pos = '%s_%s' % (seqvar.posedit.pos.start, seqvar.posedit.pos.end)
            else:
                pos = '%s' % seqvar.posedit.pos.start

        return seqtype, edittype, ref, pos, alt

    def __str__(self):
        return '%r' % self.__dict__

        
class HgvsLVG(object):

    def __init__(self, hgvs_text):
        self.hgvs_text = hgvs_text

        # use the hgvs library to get us some info about this HGVS string.
        self.seqvar = self.parse(hgvs_text)

        # fill in all the different ways to talk about this variant in each sequence type.
        self.variants = {'g': [], 'c': [], 'n': [], 'p': []}
        self.variants[self.seqvar.type] = [self.seqvar]

        for this_type, value in list(self.variants.items()):
            if value == []:
                self.variants[this_type] = [_seqvar_map_func(self.seqvar.type, this_type)(self.seqvar)]

        if self.variants['g']:
            self.transcripts = self.get_transcripts(self.variants['g'][0])

        # find out the gene name of this variant.
        self._gene_name = None

    @property
    def gene_name(self):
        if self._gene_name is None:
            if self.variants['c'] != []:
                chosen_one = self.variants['c'][0]
            elif self.variants['n'] != []:
                chosen_one = self.variants['n'][0]
            self._gene_name = variant_to_gene_name(chosen_one)
        return self._gene_name

    @staticmethod
    def get_transcripts(var_g):
        return mapper.relevant_transcripts(var_g)

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

    print(hgvs_obj)

    print()
    print(HgvsComponents(hgvs_obj.seqvar))
    print()

    for vartype in list(hgvs_obj.variants.keys()):
        print(hgvs_obj.variants[vartype])

    print()
    print(hgvs_obj.gene_name)
