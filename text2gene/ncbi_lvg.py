from __future__ import absolute_import, unicode_literals

from hgvs_lexicon import Variant, HgvsLVG

from .cached import NCBIReport


class NCBIHgvsLVG(object):

    def __init__(self, hgvs_text, **kwargs):
        self.hgvs_text = hgvs_text

        self.variants = { 'p': {}, 'c': {}, 'g': {}, 'n': {} }

        self.report = NCBIReport(self.hgvs_text)
        self._parse_report()

    def _parse_report(self):
        rep = self.report[0]
        for seqtype in self.variants.keys():
            hgvs_text = rep.get('Hgvs_%s' % seqtype, '').strip()
            if hgvs_text:
                seqvar = Variant(hgvs_text)
                self.variants[seqtype] = seqvar

    #def to_dict(self):
    #    outd = { }


class NCBIEnrichedLVG(HgvsLVG):

    def __init__(self, hgvs_text, **kwargs):
        self.variants = {'p': {}, 'c': {}, 'g': {}, 'n': {}}

        self.report = NCBIReport(str(hgvs_text))
        self._parse_report()

        super(NCBIEnrichedLVG, self).__init__(hgvs_text,
                                              hgvs_c=self.hgvs_c_variants,
                                              hgvs_g=self.hgvs_g_variants,
                                              hgvs_p=self.hgvs_p_variants,
                                              hgvs_n=self.hgvs_n_variants)

    def _parse_report(self):
        rep = self.report[0]
        for seqtype in self.variants.keys():
            hgvs_text = rep.get('Hgvs_%s' % seqtype, '').strip()
            if hgvs_text:
                seqvar = Variant(hgvs_text)
                self.variants[seqtype][str(seqvar)] = seqvar
