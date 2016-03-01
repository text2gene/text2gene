from __future__ import print_function

import warnings

from .exceptions import RejectedSeqVar

amino_acid_map = { 'Ala': 'A',
                   'Arg': 'R',
                   'Asn': 'N',
                   'Asp': 'D',
                   'Cys': 'C',
                   'Glu': 'E',
                   'Gln': 'Q',
                   'Gly': 'G',
                   'His': 'H',
                   'Ile': 'I',
                   'Leu': 'L',
                   'Lys': 'K',
                   'Met': 'M',
                   'Phe': 'F',
                   'Pro': 'P',
                   'Ser': 'S',
                   'Thr': 'T',
                   'Trp': 'W',
                   'Tyr': 'Y',
                   'Val': 'V',
                 }


class HgvsComponents(object):

    """
    Special handling when SeqType comes in empty:
        If SeqType is none and REF in [a,c,t,g] and ALT in [a,c,t,g] --> then DNA or RNA
        If SeqType is none and REF in [u] or ALT in [u] --> then RNA
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

    def infer_seqtype(ref, alt):
        if ref:
            ref = ref.lower()
        if alt:
            alt = alt.lower()

        if 'u' in ref or 'u' in alt:
            return 'g'

        if ref in ['a','c','t','g'] and alt in ['a','c','t','g']:
            return 'c'  # or 'g'?

        determinant = ref or alt
        if determinant in list(amino_acid_map.values()):
            return 'p'

    @staticmethod
    def parse(seqvar):
        """ return tuple of sequence variant components as
        (seqtype, edittype, ref, pos, alt)
        """
        if seqvar.type.strip() == '':
            warnings.warn('SequenceVariant has empty seqtype. (%r)' % seqvar)
            seqtype = ''
        else:
            seqtype = seqvar.type

        ref = alt = edittype = pos = None

        try:
            ref = seqvar.posedit.edit.ref
            alt = seqvar.posedit.edit.alt
            edittype = seqvar.posedit.edit.type.upper()
        except AttributeError:
            # seqvar has incomplete edit information. fail out.
            warnings.warn('SequenceVariant %s edit information incomplete or invalid.' % seqvar.ac)

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

        if seqtype == '':
            seqtype = self.infer_seqtype(ref, alt)

        return seqtype, edittype, ref, pos, alt

    def __str__(self):
        return '%r' % self.__dict__
