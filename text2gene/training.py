from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import pickle

import MySQLdb as mdb

from .sqlcache import SQLCache
from .cached import ClinvarCachedQuery, PubtatorCachedQuery
from .ncbi import NCBIVariantPubmedsCachedQuery, NCBIEnrichedLVGCachedQuery, NCBIHgvsLVG
from .lvg_cached import HgvsLVGCached
from .exceptions import Text2GeneError

log = logging.getLogger('text2gene.experiment')
log.setLevel(logging.DEBUG)

search_module_map = {'pubtator': PubtatorCachedQuery,
                     'clinvar': ClinvarCachedQuery,
                     'ncbi': NCBIVariantPubmedsCachedQuery,
                    }

lvg_module_map = {'ncbi_enriched': NCBIEnrichedLVGCachedQuery,
                  'lvg': HgvsLVGCached,
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

    VERSION = "0.0.1"

    def __init__(self, experiment_name, **kwargs):
        self.experiment_name = experiment_name

        self.iteration = kwargs.get('iteration', 0)

        self.lvg_mode = kwargs.get('lvg_mode', 'lvg')      # or 'ncbi' or 'ncbi_enriched'

        # normalize module names to lowercase to save on the aggravation of case-matching.
        self.search_modules = [item.lower() for item in kwargs.get('search_modules', ['pubtator', 'clinvar', 'ncbi'])]

        self.hgvs_examples_table = kwargs.get('hgvs_examples_table', None)
        self.hgvs_examples_db = kwargs.get('hgvs_examples_db', None)
        self.hgvs_examples_limit = kwargs.get('hgvs_examples_limit', None)

        self.hgvs_examples = []
        if self.hgvs_examples_table is None:
            # maybe a list was supplied instead.
            self.hgvs_examples = kwargs.get('hgvs_examples', [])

        if not self.hgvs_examples_table and not self.hgvs_examples:
            raise Text2GeneError('You need to supply either a list of hgvs_examples or database details to produce a list. (see Experiment class documentation)')

        # setup granular result tables necessary to store our results
        self._setup_tables()

        # HGVS2PMID cache-backed functions internal to this Experiment
        self.ClinvarHgvs2Pmid = ClinvarCachedQuery(granular=True, granular_table=self.get_table_name('clinvar')).query
        self.PubtatorHgvs2Pmid = PubtatorCachedQuery(granular=True, granular_table=self.get_table_name('pubtator')).query
        self.NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(granular=True, granular_table=self.get_table_name('ncbi')).query

        # set our internal LVG query function based on preference stated in kwargs.
        self.LVG = lvg_module_map[self.lvg_mode](granular_table=self.get_mapping_table_name(self.lvg_mode)).query

        super(self.__class__, self).__init__('experiment')

    @property
    def results_table_name(self):
        tname_tmpl = '{expname}_{iteration}_results'
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
        fv_dict = {'cache_key': self.get_cache_key(querydict), 'cache_value': pickle(self)}

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
                  num_pmids INT default NULL,
                  errors text default NULL
              )'''.format(tablename)
        try:
            self.execute(sql)
        except mdb.OperationalError as error:
            if error[0] == 1050:
                pass
            else:
                raise Text2GeneError('Problem creating Experiment results table %s: %r' % (self.results_table_name, error))

    def _delete_tables(self):
        for mod in self.search_modules:
            tablename = self.get_table_name(mod)
            log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, tablename)
            self.execute('drop table %s' % tablename)

        tablename = self.get_mapping_table_name(self.lvg_mode)
        log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, tablename)
        self.execute('drop table %s' % tablename)

        try:
            log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, self.results_table_name)
            self.execute('drop table %s' % self.results_table_name)
        except mdb.OperationalError as error:
            if error[0] == 1051:
                #it never got created, so that's fine.
                pass
            else:
                raise Text2GeneError('Problem deleting Experiment results table %s: %r' % (self.results_table_name, error))

    def _load_examples(self):
        sql = 'select distinct(hgvs_text) from {dbname}.{tname}'.format(dbname=self.hgvs_examples_db, tname=self.hgvs_examples_table)
        if self.hgvs_examples_limit:
            sql += ' limit %i' % self.hgvs_examples_limit
        return self.fetchall(sql)

    def store_result(self, hgvs_text, pmids, errors=None):
        row = {'hgvs_text': hgvs_text,
               'num_pmids': len(pmids),
               'errors': None if errors is None else json.dumps(errors)
               }
        self.insert(self.results_table_name, row)

    def run(self):
        # create table to track experiment progress and aggregate results from all search modules.
        self._create_experiment_results_table()

        if not self.hgvs_examples:
            # don't store a long list in memory after running, if we don't have to.
            hgvs_examples = self._load_examples()
        else:
            hgvs_examples = self.hgvs_examples

        for row in hgvs_examples:
            hgvs_text = row['hgvs_text'].strip()

            try:
                lex = self.LVG(hgvs_text, force_granular=True)
            except Exception as error:
                log.info('EXPERIMENT [%s.%i]: [%s] Error creating LVG; skipping. (Error: %r',
                                self.experiment_name, self.iteration, hgvs_text, error)
                continue

            pmids = set()
            errors = []
            for mod in self.search_modules:
                try:
                    if mod == 'clinvar':
                        result = self.ClinvarHgvs2Pmid(lex, skip_cache=True)

                    if mod == 'ncbi':
                        result = self.NCBIHgvs2Pmid(lex.hgvs_text, force_granular=True)

                    if mod == 'pubtator':
                        result = self.PubtatorHgvs2Pmid(lex, skip_cache=True)

                    log.debug('EXPERIMENT [%s.%i]: [%s] %s results: %r', self.experiment_name, self.iteration, hgvs_text, mod, result)
                except Exception as error:
                    log.debug('EXPERIMENT [%s.%i]: [%s] Error searching for matches in %s: %r',
                                    self.experiment_name, self.iteration, hgvs_text, mod, error)
                    errors.append('%r' % error)
            for pmid in result:
                pmids.add(pmid)

            log.info('EXPERIMENT [%s.%i]: [%s] All PMIDs found: %r', self.experiment_name, self.iteration, hgvs_text, pmids)
            if errors:
                log.info('EXPERIMENT [%s.%i]: [%s] %r', self.experiment_name, self.iteration, hgvs_text, errors)
            self.store_result(hgvs_text, pmids, errors=errors)

    def evaluate(self):
        """ Performs a series of MySQL queries on the match results tables to produce quantitative analysis.

        :return: dict of results
        """
        # select count(*) as cnt, count(distinct hgvs_text), count(distinct PMID) from clinvar_match;

        #
