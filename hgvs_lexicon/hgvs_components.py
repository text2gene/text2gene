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

official_to_slang_map = {'>': ['->', '-->', '/'],
                         'Ter': ['*', 'X'],
                        }

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
        self.seqvar = seqvar
        if self.seqvar:
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
            # normalize DELINS to INDEL (synonymous)
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

        #if seqvar.posedit.edit in ['?', '=']:
        if hasattr(seqvar.posedit.edit, 'lower'):
            # if the edit attribute is a str or unicode type thing:
            raise RejectedSeqVar('SequenceVariant missing edit information. (%r)' % seqvar)

        edittype = seqvar.posedit.edit.type.upper()

        try:
            ref = seqvar.posedit.edit.ref
            alt = seqvar.posedit.edit.alt
        except AttributeError as error:
            # hmm.
            log.warn('SequenceVariant %s: %s', seqvar, error)

        # if alt is a '*' it represents a Ter (STOP) sequence, which PubTator represents as an 'X'.
        if alt == '*':
            alt = 'X'

        if seqtype == 'p':
            try:
                pos = '%s' % seqvar.posedit.pos.start.pos
                ref = '%s' % seqvar.posedit.pos.start.aa
            except AttributeError:
                raise RejectedSeqVar('Protein entry incomplete (unusable).')

        else:
            if seqvar.posedit.pos.end != seqvar.posedit.pos.start:
                # compose a "range"
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

    @property
    def posedit(self):
        """ Returns the official lexeme representing this variant's position and edit information. """
        return '%s' % self.seqvar.posedit

    def _posedit_slang_protein(self):
        out = set()
        posedit = self.posedit.replace('(', '').replace(')', '')
        for item in official_to_slang_map['Ter']:
            out.add(posedit.replace('Ter', item))

        fs_pos = posedit.find('fs')
        if fs_pos > -1:
            out.add(posedit[:fs_pos + len('fs')])
        else:
            # e.g. Lys2569Gly produces "K2569G"
            out.add('%s%s%s' % (self.ref, self.pos, self.alt))
        return list(out)

    def _posedit_slang_SUB(self):
        """ Handles the Substitution case for generating posedit slang from Components. """
        # Examples based on input hgvs_text 'NM_014874.3:c.891C>T'
        out = set()

        # E.g. ["891C>T", "891C->T", "891C-->T", "891C/T"]
        for slang_symbol in official_to_slang_map['>']:
            out.add(self.posedit.replace('>', slang_symbol))

        # E.g. "C891T"
        out.add(self.ref + self.pos + self.alt)
        return list(out)

    def _posedit_slang_DEL(self):
        """ Handles the Deletion case for generating posedit slang from Components. """
        # Examples based on input hgvs_text 'NM_007294.3:c.4964_4982delCTGGCCTGACCCCAGAAGA'
        #
        # E.g. '4964_4982del'
        return [self.pos + 'del']

    def _posedit_slang_DUP(self):
        """ Handles the Duplication case for generating posedit slang from Components. """
        # Examples based on input hgvs_text 'NM_025114.3:c.6869dupA'
        #
        # E.g. '6869dup'
        return [self.pos + 'dup']

    def _posedit_slang_INDEL(self):
        """ Handles the Insertion case for generating posedit slang from Components.

        Returns an empty list (no slang terms known).
        """
        return []

    def _posedit_slang_INS(self):
        """ Handles the Insertion case for generating posedit slang from Components.

        Returns an empty list (no slang terms known).
        """
        return []

    @property
    def posedit_slang(self):
        """ If supported, returns alternative lexeme that may represent this variant's position and edit info in the wild. """
        if self.seqtype == 'p':
            return self._posedit_slang_protein()

        try:
            slang_method = getattr(self, '_posedit_slang_%s' % self.edittype)
            return slang_method()
        except AttributeError:
            raise NotImplementedError('Cannot currently handle EditType %s' % self.edittype)

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return '%r' % self.__dict__

    def __repr__(self):
        return '%r' % self.__dict__
