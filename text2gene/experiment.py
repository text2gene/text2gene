from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import pickle

import MySQLdb as mdb

from metavariant.utils import strip_gene_name_from_hgvs_text
from metavariant.exceptions import CriticalHgvsError

from .sqlcache import SQLCache
from .cached import ClinvarCachedQuery, PubtatorCachedQuery
from .googlequery import GoogleCachedQuery, googlecse2pmid
from .ncbi import NCBIVariantPubmedsCachedQuery, NCBIEnrichedLVGCachedQuery
from .lvg_cached import VariantLVGCached
from .exceptions import Text2GeneError
from .report_utils import hgvs_to_clinvar_variationID

log = logging.getLogger('text2gene.experiment')
log.setLevel(logging.DEBUG)

search_module_map = {'pubtator': PubtatorCachedQuery,
                     'clinvar': ClinvarCachedQuery,
                     'ncbi': NCBIVariantPubmedsCachedQuery,
                     'google': GoogleCachedQuery
                    }

lvg_module_map = {'ncbi_enriched': NCBIEnrichedLVGCachedQuery,
                  'lvg': VariantLVGCached,
                 }  # can't support 'ncbi' yet -- its cache class doesn't organically match the others, yet.


class Experiment(SQLCache):

    """
    Example that could be run from ./api-shell:

        experiment = Experiment('crazy_harebrained_scheme', iteration=42, hgvs_examples=[hgvs_text_c1, hgvs_text_c2])
        experiment.run()

    Note that "iteration" is an optional, arbitrary qualifier which defaults to 0 and only affects table names.

    In the above example, the Experiment object will set up these tables:

        * crazy_harebrained_scheme_42_clinvar_match
        * crazy_harebrained_scheme_42_ncbi_match
        * crazy_harebrained_scheme_42_pubtator_match
        * crazy_harebrained_scheme_42_google_match
        * crazy_harebrained_scheme_42_lvg_mappings

    Results in the above tables for the search_modules (able to be specified via keyword argument) consist of
    hgvs_text -> PMID pairings based on the results achieved for given HGVS string using given search method.

    To change the LVG function used, supply the following keyword:

        lvg_mode        # one of ['lvg', 'ncbi_enriched']

    Results for the lvg_mappings (or ncbi_enriched_mappings) consist of a breakdown of input hgvs_text -> one of
    hgvs_c, hgvs_g, hgvs_n, hgvs_p.  So if an input HGVS string had 1 of each different type of variant mappings,
    the *_mappings table would contain four separate rows with the same hgvs_text (and a different variant result per row).

    A list of HGVS strings must be supplied to run an experiment.

    If reading examples from the database, these two keyword arguments are needed:

        hgvs_examples_table
        hgvs_examples_db

    ...and optionally, supply a limit to the number of examples to draw from the table (default is no limit):
        hgvs_examples_limit


    If supplying examples from a list, feed the list into this keyword argument:

        hgvs_examples

    NOTE that database details are preferred over a supplied list. The list will be ignored if DB details are supplied.

    If neither source of HGVS examples is supplied, a Text2Gene error is raised in complaint.
    """

    VERSION = 1

    def __init__(self, experiment_name, **kwargs):
        self.experiment_name = experiment_name

        self.iteration = kwargs.get('iteration', 0)

        self.skip_cache = kwargs.get('skip_cache', False)

        self.lvg_mode = kwargs.get('lvg_mode', 'ncbi_enriched')      # or 'ncbi' or 'ncbi_enriched'

        # normalize module names to lowercase to save on the aggravation of case-matching.
        self.search_modules = [item.lower() for item in kwargs.get('search_modules', ['pubtator', 'clinvar', 'ncbi', 'google'])]

        self.hgvs_examples_table = kwargs.get('hgvs_examples_table', None)
        self.hgvs_examples_db = kwargs.get('hgvs_examples_db', None)
        self.hgvs_examples_limit = kwargs.get('hgvs_examples_limit', None)

        self.hgvs_examples = []
        if self.hgvs_examples_table is None:
            # maybe a list was supplied instead.
            self.hgvs_examples = kwargs.get('hgvs_examples', [])

        if not self.hgvs_examples_table and not self.hgvs_examples:
            raise Text2GeneError('You need to supply either a list of hgvs_examples or database details to produce a list. (see Experiment class documentation)')

        # HGVS2PMID cache-backed functions internal to this Experiment
        self.ClinvarHgvs2Pmid = ClinvarCachedQuery(granular=True, granular_table=self.get_table_name('clinvar')).query
        self.PubtatorHgvs2Pmid = PubtatorCachedQuery(granular=True, granular_table=self.get_table_name('pubtator')).query
        self.NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(granular=True, granular_table=self.get_table_name('ncbi')).query
        self.GoogleQuery = GoogleCachedQuery(granular=True, granular_table=self.get_table_name('google')).query

        # set our internal LVG query function based on preference stated in kwargs.
        #self.LVG = lvg_module_map[self.lvg_mode](granular_table=self.get_mapping_table_name(self.lvg_mode)).query

        #if self.lvg_mode=='ncbi_enriched':
        self.LVG = NCBIEnrichedLVGCachedQuery(granular_table=self.get_mapping_table_name(self.lvg_mode)).query
        #else:
        #    self.LVG = VariantLVGCached(granular_table=self.get_mapping_table_name(self.lvg_mode)).query

        super(self.__class__, self).__init__('experiment')

    @property
    def results_table_name(self):
        tname_tmpl = '{expname}_{iteration}_results'
        return tname_tmpl.format(expname=self.experiment_name, iteration=self.iteration)

    @property
    def summary_table_name(self):
        tname_tmpl = '{expname}_{iteration}_summary'
        return tname_tmpl.format(expname=self.experiment_name, iteration=self.iteration)

    def get_table_name(self, module_name):
        """ Produce a table name for given module_name, based on this Experiment's experiment_name and iteration.

        :return: (str) table name for this experiment and iteration, given module_name
        """
        tname_tmpl = '{expname}_{iteration}_{mod}_match'
        return tname_tmpl.format(expname=self.experiment_name, iteration=self.iteration, mod=module_name)

    def get_mapping_table_name(self, lvg_mode):
        tname_tmpl = '{expname}_{iteration}_{lvg}_mappings'
        return tname_tmpl.format(expname=self.experiment_name, iteration=self.iteration, lvg=lvg_mode)

    def to_dict(self):
        return {'experiment_name': self.experiment_name,
                'search_modules': self.search_modules,
                'iteration': self.iteration,
                'lvg_mode': self.lvg_mode
                }

    def cache(self, **kwargs):
        """ Store current state of experiment in database as cache_key (hashed pickle of self.to_dict() ->
        cache_value (pickled object).

        Keywords:
            update_if_duplicate: when True: if item with same cache_key found, update value.

        :return: True if successful, False otherwise
        """
        querydict = self.to_dict()
        fv_dict = {'cache_key': self.get_cache_key(querydict), 'cache_value': pickle.dumps(self)}

        try:
            self.insert(self.tablename, fv_dict)
        except mdb.IntegrityError:
            if kwargs.get('update_if_duplicate', True):
                # update entry with current time
                return self.update(fv_dict)
            else:
                return False

        return True

    def _setup_tables(self):
        """ Creates experiment tables in text2gene database for all search_modules used in this Experiment.
        :return: None
        """
        for mod in self.search_modules:
            tablename = self.get_table_name(mod)
            log.debug('EXPERIMENT %s: creating table %s for %s', self.experiment_name, tablename, mod)
            search_module_map[mod](granular=True, granular_table=tablename).create_granular_table()

        # create LVG mapping table
        tablename = self.get_mapping_table_name(self.lvg_mode)
        log.debug('EXPERIMENT %s: creating LVG mapping table %s', self.experiment_name, tablename)
        lvg_module_map[self.lvg_mode](granular=True, granular_table=tablename).create_granular_table()

    def _create_experiment_results_table(self):
        tablename = self.results_table_name
        log.debug('EXPERIMENT %s: creating Experiment results table %s', self.experiment_name, tablename)
        self.execute('drop table if exists %s' % self.results_table_name)
        sql = '''create table {} (
                  id int(11) primary key auto_increment,
                  hgvs_text varchar(255) unique,
                  gene_name varchar(255) default NULL,
                  num_pmids INT default NULL,
                  errors text default NULL
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci'''.format(tablename)
        try:
            self.execute(sql)
        except mdb.OperationalError as error:
            if error[0] == 1050:
                pass
            else:
                raise Text2GeneError('Problem creating Experiment results table %s: %r' % (self.results_table_name, error))

    def _create_experiment_summary_table(self):
        tablename = self.summary_table_name
        log.debug('EXPERIMENT %s: creating Experiment summary table %s', self.experiment_name, tablename)
        self.execute('drop table if exists %s' % self.summary_table_name)
        sql = '''create table {} (
                  hgvs_text       varchar(255) not null,
                  VariationID     int default null,
                  gene_name       varchar(50) default null,
                  PMID            int default null,
                  match_clinvar   boolean default 0,
                  match_ncbi      boolean default 0,
                  match_pubtator  boolean default 0,
                  match_google    boolean default 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci'''.format(tablename)
        try:
            self.execute(sql)
        except mdb.OperationalError as error:
            if error[0] == 1050:
                pass
            else:
                raise Text2GeneError('Problem creating Experiment results table %s: %r' % (self.results_table_name, error))

    def _delete_tables(self):
        """ Still a little risky to use! """
        for mod in self.search_modules:
            tablename = self.get_table_name(mod)
            log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, tablename)
            self.drop_table(tablename)

        tablename = self.get_mapping_table_name(self.lvg_mode)
        log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, tablename)
        self.drop_table(tablename)

        log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, self.results_table_name)
        self.drop_table(self.results_table_name)
        self.drop_table(self.summary_table_name)

    def _load_examples(self):
        sql = 'select distinct(hgvs_text) from {dbname}.{tname}'.format(dbname=self.hgvs_examples_db, tname=self.hgvs_examples_table)
        if self.hgvs_examples_limit:
            sql += ' limit %i' % self.hgvs_examples_limit
        return self.fetchall(sql)

    def store_result(self, hgvs_text, pmids, gene_name=None, errors=None):
        row = {'hgvs_text': hgvs_text,
               'num_pmids': len(pmids),
               'gene_name': gene_name,
               'errors': None if errors is None else json.dumps(errors)
               }
        self.insert(self.results_table_name, row)

    def run(self):
        # setup each search_module's granular result table
        self._setup_tables()

        # create table to track experiment progress and aggregate results from all search modules.
        self._create_experiment_results_table()
        self._create_experiment_summary_table()

        if not self.hgvs_examples:
            # don't store a long list in memory after running, if we don't have to.
            hgvs_examples = self._load_examples()
        else:
            hgvs_examples = self.hgvs_examples

        total_examples = len(hgvs_examples)
        index = 0
        for item in hgvs_examples:
            index += 1

            if hasattr(item, 'upper'):
                # assume this is a string from a list
                hgvs_text = str(item).strip()
            else:
                # assume this is a row from mysql
                hgvs_text = item['hgvs_text'].strip()

            # make sure we're storing cache results with non-gene-containing hgvs strings as the key.
            hgvs_text = strip_gene_name_from_hgvs_text(hgvs_text)
            log.info('EXPERIMENT [%s.%i]: %i / %i' % (self.experiment_name, self.iteration, index, total_examples))

            try:
                lex = self.LVG(hgvs_text, force_granular=True)
                #print(lex.gene_name)
            except Exception as error:
                log.info('EXPERIMENT [%s.%i]: [%s] Error creating LVG; skipping. (Error: %r',
                                self.experiment_name, self.iteration, hgvs_text, error)
                continue

            pmids = set()
            errors = []
            summary_table = {}
            for mod in self.search_modules:
                summary_table[mod] = []
                result = []
                try:
                    if mod == 'clinvar':
                        result = self.ClinvarHgvs2Pmid(lex, force_granular=True, skip_cache=self.skip_cache)

                    if mod == 'ncbi':
                        result = self.NCBIHgvs2Pmid(lex.hgvs_text, force_granular=True)

                    if mod == 'pubtator':
                        result = self.PubtatorHgvs2Pmid(lex, force_granular=True, skip_cache=self.skip_cache)

                    if mod == 'google':
                        cse_results = self.GoogleQuery(lex, force_granular=True, skip_cache=self.skip_cache)
                        result = googlecse2pmid(cse_results)

                    log.debug('EXPERIMENT [%s.%i]: [%s] %s results: %r', self.experiment_name, self.iteration, hgvs_text, mod, result)
                except Exception as error:
                    log.debug('EXPERIMENT [%s.%i]: [%s] Error searching for matches in %s: %r',
                                    self.experiment_name, self.iteration, hgvs_text, mod, error)
                    errors.append('%r' % error)
                    #if 'GoogleQueryMissingGeneName' in '%r' % error:
                    #    from IPython import embed; embed()

                for pmid in result:
                    pmids.add(pmid)
                    summary_table[mod].append(pmid)

            log.info('EXPERIMENT [%s.%i]: [%s] All PMIDs found: %r', self.experiment_name, self.iteration, hgvs_text, pmids)
            if errors:
                log.info('EXPERIMENT [%s.%i]: [%s] %r', self.experiment_name, self.iteration, hgvs_text, errors)

            self.store_result(hgvs_text, pmids, gene_name=lex.gene_name, errors=errors)
            self.store_summary(hgvs_text, summary_table, pmids, lex.gene_name)

    def get_all_results(self):
        return self.fetchall('select * from {}'.format(self.results_table_name))

    def get_results_for_search_module(self, hgvs_text, mod):
        tablename = self.get_table_name(mod)
        return self.fetchall('select * from {} where hgvs_text="{}"'.format(tablename, hgvs_text))

    def store_summary(self, hgvs_text, summary_table, pmids, gene_name=None):
        # Summary Table: { mod_name: [list of pmids] }
        #
        varID = hgvs_to_clinvar_variationID(hgvs_text)

        row_tmpl = {'hgvs_text': hgvs_text,
                    'PMID': None,
                    'VariationID': varID,
                    'gene_name': gene_name,
                    'match_pubtator': 0,
                    'match_ncbi': 0,
                    'match_clinvar': 0,
                    'match_google': 0
                    }

        for pmid in pmids:
            row = row_tmpl.copy()
            row['PMID'] = pmid
            for mod in self.search_modules:
                if pmid in summary_table[mod]:
                    row['match_%s' % mod] = 1
            self.insert(self.summary_table_name, row)

