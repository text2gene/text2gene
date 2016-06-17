from __future__ import absolute_import, unicode_literals

import pickle
import logging
import urllib

import requests

from metavariant import Variant, VariantLVG
from metavariant.exceptions import CriticalHgvsError

from .sqlcache import SQLCache
from .config import GRANULAR_CACHE
from .exceptions import Text2GeneError, NCBIRemoteError

log = logging.getLogger('text2gene.ncbi')


def ncbi_report_to_variants(report):
    """ Parses Hgvs_* strings from NCBI report and creates a "variants" dictionary
    like the following (mimicking the VariantLVG.variants attribute):

    {seqtype: { 'hgvs_string': SequenceVariant object }

    :param report: list of strings representing NCBI Variation Reporter output
    :return: dict as per structure above
    """
    variants = {'p': {}, 'c': {}, 'g': {}, 'n': {}, 'm': {}, 'r': {}}
    for rep_part in report:
        for seqtype in variants.keys():
            hgvs_text = rep_part.get('Hgvs_%s' % seqtype, '').strip()
            if hgvs_text:
                # set up data structure just like VariantLVG object, i.e.:
                # {seqtype: { 'hgvs_string': SequenceVariant object }
                seqvar = Variant(hgvs_text)
                if seqvar:
                    # Sometimes NCBI has variant strings that do not parse. Variant() function returns None in these cases.
                    variants[seqvar.type][str(seqvar)] = seqvar

    return variants


def ncbi_report_to_pubmeds(report):
    """ Parses PMIDs from NCBI report and returns as list of strings.

    :param report: list of strings representing NCBI Variation Reporter output
    :return: list of pubmeds found in report
    """
    return [int(item) for item in report[0]['PMIDs']]


def get_ncbi_variant_report(hgvs_text):
    """
    Return results from API query to the NCBI Variant Reporter Service
    See documentation at:
    http://www.ncbi.nlm.nih.gov/variation/tools/reporter

    :param hgvs_text: ( c.DNA | r.RNA | p.Protein | g.Genomic )
    :return: list containing each dict of parsed results
    """
    response = requests.get("http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi?annot1={}".format(urllib.quote(hgvs_text)))

    if 'Error' in response.text:
        error_str = 'The NCBI Variant Report Service returned an error: "{}"\n'.format(response.text)
        error_str += 'To reproduce, visit: http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi?annot1={}'.format(hgvs_text)
        raise NCBIRemoteError(error_str)

    keys = []
    report = []

    for line in response.text.split('\n'):
        if not line.strip() or line.startswith('.') or line.startswith('##') or line.startswith('Submitted'):
            continue

        if line.startswith('# '):
            keys = line.strip('# ').split('\t')
        else:
            values = line.split('\t')
            outd = dict(zip(keys, values))

            # convert PMIDs from semicolon- or comma-separated string into python list
            if len(outd.get('PMIDs', '')) > 0:
                outd['PMIDs'] = outd['PMIDs'].replace(', ', ';').split(';')
            report.append(outd)

    if report == []:
        raise NCBIRemoteError('The NCBI Variant Report Service returned an empty report.\nTo reproduce, visit: http://www.ncbi.nlm.nih.gov/projects/SNP/VariantAnalyzer/var_rep.cgi?annot1={}'.format(hgvs_text))

    return report


class NCBIHgvsLVG(object):

    """ Creates a pseudo-LVG object with a bare-bones assortment of attributes, using data
    drawn from an NCBIReport lookup. (Uses NCBI cache, but is not itself a cached LVG object.)

        .hgvs_text      hgvs string representing input variant
        .seqvar         SequenceVariant object representing input variant
        .variants       dictionary resembling VariantLVG.variants
        .report         copy of NCBI report; safe since this is not a cached object
        .kwargs         accepts arbitrary input kwargs to mimic the "real" LVG objects

    Examples:
        ncbi_lex = NCBIHgvsLVG('NM_000249.3:c.1958T>G')

        seqvar = Variant('NM_000249.3:c.1958T>G')
        ncbi_lex = NCBIHgvsLVG(seqvar)
    """

    VERSION = 0
    LVG_MODE = 'ncbi'

    def __init__(self, hgvs_text_or_seqvar, **kwargs):
        self.hgvs_text = '%s' % hgvs_text_or_seqvar
        self.seqvar = Variant(hgvs_text_or_seqvar)
        if self.seqvar is None:
            raise CriticalHgvsError('Cannot create SequenceVariant from input %s (see hgvs_lexicon log)' % self.hgvs_text)
        self.report = NCBIReport(self.hgvs_text)
        self.variants = ncbi_report_to_variants(self.report)
        self.kwargs = kwargs


class NCBIEnrichedLVG(VariantLVG):

    """ Creates a true LVG object by subclassing from VariantLVG and using data drawn from an NCBIReport
    lookup.  See VariantLVG (from metavariant) for additional documentation.

    *** ! To use the cached version of this object, use LVGEnriched ! ***

    Examples:
        lex = NCBIEnrichedLVG('NM_000249.3:c.1958T>G')

        seqvar = Variant('NM_000249.3:c.1958T>G')
        lex = NCBIEnrichedLVG(seqvar)
    """

    VERSION = 1
    LVG_MODE = 'ncbi_enriched'

    def __init__(self, hgvs_text_or_seqvar, **kwargs):
        self.hgvs_text = '%s' % hgvs_text_or_seqvar
        self.seqvar = Variant(hgvs_text_or_seqvar)
        self.ncbierror = None
        if self.seqvar is None:
            raise CriticalHgvsError('Cannot create SequenceVariant from input %s (see hgvs_lexicon log)' % self.hgvs_text)
        try:
            report = NCBIReport(self.hgvs_text)
            self.variants = ncbi_report_to_variants(report)
        except NCBIRemoteError as error:
            log.debug('Skipping NCBI enrichment; %r' % error)
            self.ncbierror = '%r' % error
            self.error = ''
            self.variants = {'c': {}, 'g': {}, 'p': {}, 'n': {}}
            self.variants[self.seqvar.type][self.hgvs_text] = self.seqvar

        super(NCBIEnrichedLVG, self).__init__(self.hgvs_text,
                                              hgvs_c=self.hgvs_c,
                                              hgvs_g=self.hgvs_g,
                                              hgvs_p=self.hgvs_p,
                                              hgvs_n=self.hgvs_n,
                                              kwargs=kwargs)


class NCBIEnrichedLVGCachedQuery(SQLCache):

    VERSION = 1

    def __init__(self, granular=False, granular_table='ncbi_enriched_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_enriched_lvg')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def get_cache_value(self, obj):
        """ Returns pickled object representation of supplied object. """
        return pickle.dumps(obj)

    def retrieve(self, hgvs_text, version=0):
        """ If cache contains a value for hgvs_text, retrieve it. Otherwise, return None.

        (Overrides default retrieve)

        If requested version number is GREATER THAN OR EQUAL TO version number of existing data, older version will be
        destroyed so that newer version can be created in its place.

        Thus, supplying version=0 allows returns from cache from *any* version of data that has ever been stored.

        :param hgvs_text: (str)
        :param version: (int) only return results from cache with greater than or equal version number [default: 0]
        :return: LVG object or None
        """
        row = self.get_row(hgvs_text)
        if row:
            if row['version'] >= version:
                return pickle.loads(row['cache_value'])
            else:
                log.debug('Expiring obsolete entry at cache_key location %s.', self.get_cache_key(hgvs_text))
                self.delete(hgvs_text)
        return None

    def _store_granular_hgvs_type(self, lex, hgvs_seqtype_name):
        hgvs_vars = getattr(lex, hgvs_seqtype_name)
        if hgvs_vars:
            entry_pairs = [{'hgvs_text': lex.hgvs_text,
                            hgvs_seqtype_name: item,
                            'version': self.VERSION} for item in hgvs_vars]

            self.batch_insert(self.granular_table, entry_pairs)

    def store_granular(self, lex):
        for hgvs_type in ['c', 'g', 'n', 'p']:
            self._store_granular_hgvs_type(lex, 'hgvs_'+hgvs_type)

    def query(self, hgvs_text, skip_cache=False, force_granular=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(result)
                return result

        lexobj = NCBIEnrichedLVG(hgvs_text)
        if lexobj:
            self.store(hgvs_text, lexobj)
            if force_granular or self.granular:
                self.store_granular(lexobj)
            return lexobj
        else:
            raise Text2GeneError('NCBIEnrichedLVG object could not be created from input hgvs_text %s' % hgvs_text)

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for NCBIEnrichedLVGCachedQuery'.format(tname))

        self.execute("drop table if exists {};".format(tname))

        sql = """create table {} (
              hgvs_text varchar(255) not null,
              hgvs_g varchar(255) default NULL,
              hgvs_c varchar(255) default NULL,
              hgvs_n varchar(255) default NULL,
              hgvs_p varchar(255) default NULL,
              version varchar(10) default NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)

        self.execute('call create_index("{}", "hgvs_text,hgvs_g")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_c")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_n")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_p")'.format(tname))


class NCBIVariantPubmedsCachedQuery(SQLCache):

    VERSION = 0

    def __init__(self, granular=False, granular_table='ncbi_match'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_hgvs2pmid')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def store_granular(self, hgvs_text, result):
        entry_pairs = [{'hgvs_text': hgvs_text, 'PMID': pmid, 'version': self.VERSION} for pmid in result]
        self.batch_insert(self.granular_table, entry_pairs)

    def query(self, hgvs_text, skip_cache=False, force_granular=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(hgvs_text, result)
                return result

        report = NCBIReport(hgvs_text, skip_cache)
        result = ncbi_report_to_pubmeds(report)
        self.store(hgvs_text, result)
        if (force_granular or self.granular) and result:
            self.store_granular(hgvs_text, result)
        return result

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for NCBIVariantPubmedsCachedQuery'.format(tname))

        self.execute("drop table if exists {}".format(tname))

        sql = """create table {} (
                  hgvs_text varchar(255) not null,
                  PMID int(11) default NULL,
                  version varchar(10) default NULL)
                  ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)
        sql = 'call create_index("{}", "hgvs_text,PMID")'.format(tname)
        self.execute(sql)


class NCBIVariantReportCachedQuery(SQLCache):

    VERSION = 0

    MAXIMUM_REPORT_ENTRIES = 6

    def __init__(self, granular=False, granular_table='ncbi_mappings'):
        self.granular = granular
        self.granular_table = granular_table
        super(self.__class__, self).__init__('ncbi_report')

    def get_cache_key(self, hgvs_text):
        return str(hgvs_text)

    def _limit_report(self, report):
        """ Limit length of report to MAXIMUM_REPORT_ENTRIES records.

        Usually doesn't matter (most reports have at most 2 entries), but there are some
        freaks with 60+ (!).

        See tests/demo_NCBI_long_report_examples.py

        We find that the last usual location of unique variant info is at report index 5.
        If we try to keep these huge reports at full size, we can't cache them in SQL tables.

        :param: report (list of dictionaries)
        :return: report (list of dictionaries) possibly reduced in length.
        """
        if len(report) > self.MAXIMUM_REPORT_ENTRIES:
            return report[:self.MAXIMUM_REPORT_ENTRIES]
        else:
            return report

    def _store_granular_hgvs_type(self, hgvs_text, hgvs_vars, seqtype):
        entry_pairs = [{'hgvs_text': hgvs_text,
                        'hgvs_%s' % seqtype: '%s' % item,
                        'version': self.VERSION} for item in hgvs_vars]

        self.batch_insert(self.granular_table, entry_pairs)

    def store_granular(self, hgvs_text, result):
        variants = ncbi_report_to_variants(result)
        for seqtype in variants.keys():
            if variants[seqtype]:
                # if there's a variant actually in there (sometimes there's not)...
                self._store_granular_hgvs_type(hgvs_text, variants[seqtype], seqtype)

    def query(self, hgvs_text, skip_cache=False, force_granular=False):
        if not skip_cache:
            result = self.retrieve(hgvs_text, version=self.VERSION)
            if result:
                if force_granular:
                    self.store_granular(hgvs_text, result)
                return result

        report = self._limit_report(get_ncbi_variant_report(hgvs_text))
        self.store(hgvs_text, report)
        if force_granular or self.granular:
            self.store_granular(hgvs_text, report)
        return report

    def create_granular_table(self):
        tname = self.granular_table
        log.info('creating table {} for NCBIVariantReportCachedQuery'.format(tname))

        self.execute("drop table if exists {};".format(tname))

        sql = """create table {} (
              hgvs_text varchar(255) not null,
              hgvs_g varchar(255) default NULL,
              hgvs_c varchar(255) default NULL,
              hgvs_n varchar(255) default NULL,
              hgvs_p varchar(255) default NULL,
              version varchar(10) default NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(tname)
        self.execute(sql)

        self.execute('call create_index("{}", "hgvs_text,hgvs_g")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_c")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_n")'.format(tname))
        self.execute('call create_index("{}", "hgvs_text,hgvs_p")'.format(tname))


# == API Functions == #

NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(granular=GRANULAR_CACHE).query
NCBIReport = NCBIVariantReportCachedQuery(granular=GRANULAR_CACHE).query
LVGEnriched = NCBIEnrichedLVGCachedQuery(granular=GRANULAR_CACHE).query
