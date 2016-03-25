from __future__ import print_function, unicode_literals

import logging

from .config import PKGNAME
from .exceptions import RejectedSeqVar

log = logging.getLogger(PKGNAME)

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

dna_nucleotides = ['A','C','T','G']
#rna_nucleotides = ['A','C','U','G']

class HgvsComponents(object):

    """
    #######################################################################
    # Mutation2Pubtator SeqTypes --> the higher count SeqTypes are higher priority.
    # Note that many SeqType are null, and therefore need to be implied!
    # Amino Acids List
    # List of the 20 protein (amino acids)
    # http://www.cryst.bbk.ac.uk/education/AminoAcid/the_twenty.html
    # If SeqType is none and REF in [u] or ALT in [u] --> then RNA
    # If SeqType is none and REF in [AminoAcidsList] and ALT in [AminoAcidsList] --> then Protein
    # If SeqType is none and REF in [a,c,t,g] and ALT in [a,c,t,g] --> then DNA or RNA
    #
    # JIRA: https://text2gene.atlassian.net/browse/T2G-3
    """

    def __init__(self, seqvar=None, **kwargs):
        if seqvar:
            self.seqtype, self.edittype, self.ref, self.pos, self.alt = self.parse(seqvar)
            #TODO: get FS_Pos and DupX out of seqvar when applicable.
        else:
            # names of keywords match capitalization used in MySQL m2p_* tables in pubtatordb
            self.seqtype = kwargs.get('SeqType', '').strip()
            self.edittype = kwargs.get('EditType', '').strip()
            self.ref = kwargs.get('Ref', '').strip()
            self.pos = kwargs.get('Pos', '').strip()
            self.alt = kwargs.get('Alt', '').strip()
            self.fs_pos = kwargs.get('FS_Pos', '').strip()
            self.dupx = kwargs.get('DupX', '').strip()

        if self.edittype.upper() == 'DELINS':
            # normalize DELINS to INDEL (these are synonyms)
            self.edittype = 'INDEL'

        if not self.seqtype:
            self.seqtype = self._infer_seqtype()

    def _infer_seqtype(self):
        refalt = self.ref.upper() + self.alt.upper()

        if 'u' in refalt:
            # Definitely RNA: there's no "U" amino acid and no "U" in the DNA nucleotides.
            return 'n'

        for char in refalt:
            if char not in dna_nucleotides:
                if char in list(amino_acid_map.values()):
                    return 'p'

        # it's "probably" DNA, but we can't know for sure.
        return ''

    @staticmethod
    def parse(seqvar):
        """ return tuple of sequence variant components as
        (seqtype, edittype, ref, pos, alt)
        """
        if seqvar.type.strip() == '':
            log.warn('SequenceVariant has empty seqtype. (%r)' % seqvar)
            seqtype = ''
        else:
            seqtype = seqvar.type

        ref = alt = edittype = pos = ''

        if seqvar.posedit.edit in ['?', '=']:
            raise RejectedSeqVar('SequenceVariant has missing edittype. (%r)' % seqvar)

        edittype = seqvar.posedit.edit.type.upper()

        try:
            ref = seqvar.posedit.edit.ref
            alt = seqvar.posedit.edit.alt
        except AttributeError:
            # hmm.
            log.warn('SequenceVariant %s edit information incomplete or invalid.' % seqvar.ac)

        if seqtype == 'p':
            try:
                pos = '%s' % seqvar.posedit.pos.start.pos
                ref = '%s' % seqvar.posedit.pos.start.aa
            except AttributeError:
                raise RejectedSeqVar('Protein entry incomplete (unusable).')

        else:
            if seqvar.posedit.pos.end != seqvar.posedit.pos.start:
                # compose a "range" for
                pos = '%s_%s' % (seqvar.posedit.pos.start, seqvar.posedit.pos.end)
            else:
                pos = '%s' % seqvar.posedit.pos.start

        return seqtype, edittype, ref, pos, alt

    def to_mysql_dict(self):
        outd = { 'Ref': self.ref,
                 'Alt': self.alt,
                 'SeqType': self.seqtype,
                 'EditType': self.edittype,
                 'Pos': self.pos,
                 }
        if self.edittype == 'FS':
            outd['FS_Pos'] = self.fs_pos

        if self.edittype == 'DUP':
            outd['DupX'] = self.dupx

        return outd

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return '%r' % self.__dict__
