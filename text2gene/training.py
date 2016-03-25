from __future__ import absolute_import, print_function, unicode_literals

import logging
import pickle

import MySQLdb as mdb

from .sqlcache import SQLCache
from .cached import ClinvarCachedQuery, PubtatorCachedQuery
from .ncbi import NCBIVariantPubmedsCachedQuery, NCBIEnrichedLVGCachedQuery, NCBIHgvsLVG
from .lvg_cached import HgvsLVGCached

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

        if self.hgvs_examples_table is None:
            # maybe a list was supplied instead.
            self.hgvs_examples = kwargs.get('hgvs_examples', [])

        if not self.hgvs_examples_table and not self.hgvs_examples:
            raise Text2GeneError('You need to supply either a list of hgvs_examples or database details to produce a list. (see Experiment doc)')

        # setup granular result tables necessary to store our results
        self._setup_tables()

        # HGVS2PMID cache-backed functions internal to this Experiment
        self.ClinvarHgvs2Pmid = ClinvarCachedQuery(granular=True, granular_table=self.get_table_name('clinvar')).query
        self.PubtatorHgvs2Pmid = PubtatorCachedQuery(granular=True, granular_table=self.get_table_name('pubtator')).query
        self.NCBIHgvs2Pmid = NCBIVariantPubmedsCachedQuery(granular=True, granular_table=self.get_table_name('ncbi')).query

        # set our internal LVG query function based on preference stated in kwargs.
        self.LVG = lvg_module_map[self.lvg_mode](granular_table=self.get_mapping_table_name(self.lvg_mode)).query

        super(self.__class__, self).__init__('experiment')

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
        fv_dict = {'cache_key': self.get_cache_key(querydict), 'cache_value': pickle(self) }

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

    def _delete_tables(self):
        for mod in self.search_modules:
            tablename = self.get_table_name(mod)
            log.info('EXPERIMENT [%s.%i] !!! DROPPING TABLE %s', self.experiment_name, self.iteration, tablename)
            self.execute('drop table %s' % tablename)

        self.execute('drop table %s' % self.get_mapping_table_name(self.lvg_mode))

    def _load_examples(self):
        sql = 'select * from {dbname}.{tname}'.format(dbname=self.hgvs_examples_db, tname=self.hgvs_examples_table)
        if self.hgvs_examples_limit:
            sql += ' limit %i' % self.hgvs_examples_limit
        return self.fetchall(sql)

    def run(self):
        for row in self._load_examples():
            hgvs_text = row['hgvs_text'].strip()

            try:
                lex = self.LVG(hgvs_text, force_granular=True)
            except Exception as error:
                log.info('EXPERIMENT [%s.%i]: [%s] Error creating LVG; skipping. (Error: %r',
                                self.experiment_name, self.iteration, hgvs_text, error)
                continue

            for mod in self.search_modules:
                try:
                    if mod == 'clinvar':
                        result = self.ClinvarHgvs2Pmid(lex, skip_cache=True)

                    if mod == 'ncbi':
                        result = self.NCBIHgvs2Pmid(lex.hgvs_text, force_granular=True)

                    if mod == 'pubtator':
                        result = self.PubtatorHgvs2Pmid(lex, skip_cache=True)

                    log.info('EXPERIMENT [%s.%i]: [%s] %s results: %r', self.experiment_name, self.iteration, hgvs_text, mod, result)
                except Exception as error:
                    log.info('EXPERIMENT [%s.%i]: [%s] Error searching for matches in %s: %r',
                                    self.experiment_name, self.iteration, hgvs_text, mod, error)

    def evaluate(self):
        """ Performs a series of MySQL queries on the match results tables to produce quantitative analysis.

        :return: dict of results
        """
        pass
