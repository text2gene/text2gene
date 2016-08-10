from __future__ import absolute_import, unicode_literals

import hashlib
import pickle
import json
import logging
from datetime import datetime

import MySQLdb as mdb

from medgen.config import config as medgen_config

from pubtatordb.sqldata import SQLData, SQLdatetime

log = logging.getLogger('text2gene.sqlcache')


class SQLCache(SQLData):
    """ Subclass of SQLData that stores simple key-value pairs on a unique-key-indexed
    table within the text2gene database.  (Needs to already exist with same authorization
    params as medgen.)  The table can be dynamically created
    """

    DBNAME = 'text2gene'
    DBUSER = medgen_config.get('medgen', 'db_user')
    DBPASS = medgen_config.get('medgen', 'db_pass')
    DBHOST = medgen_config.get('medgen', 'db_host')
    DBPORT = medgen_config.get('medgen', 'db_port')

    TABLENAME_FORMAT = '{}_cache'

    VERSION = 0

    def __init__(self, servicename, *args, **kwargs):
        self._db_host = self.DBHOST
        self._db_user = self.DBUSER
        self._db_pass = self.DBPASS
        self._db_name = self.DBNAME
        self.commitOnEnd = True

        self.servicename = servicename
        self.tablename = kwargs.get('tablename', self.TABLENAME_FORMAT.format(self.servicename))

    def get_cache_key(self, querydict):
        """ Default method to make a unique cache key from an input dictionary.
        """
        return hashlib.md5(pickle.dumps(sorted(querydict.items()))).hexdigest()

    def get_cache_value(self, value):
        """ Default method to turn a serializable data structure into a storable and
        reconstructable mysql blob value.  (Uses json.dumps and strips out literal "\'")
        """
        return json.dumps(value).replace("\'", '')        # get rid of literal "\'" which mysql will choke on.

    def update(self, fv_dict):
        """
        :param fv_dict: field-value dictionary with values intended to replace existing entry at cache_key
        :return: True if successful
        :raises: MySQLdb exceptions
        """
        sql = "update {db.tablename} set cache_value=%s where cache_key=%s".format(db=self, **fv_dict)
        self.execute(sql, *(fv_dict['cache_value'], fv_dict['cache_key']))
        return True

    def store(self, querydict, value, **kwargs):
        """ Takes a query dictionary containing "defining arguments" for the resultant value to be cached and the value,
        stores this as cache_key - cache_value in the cache DB.

        The value MUST be serializable to a string. (json.dumps will be used)

        If an entry with previously stored querydict exists, entry will be updated with date_created set to datetime.now()
        This behavior can be changed to ignoring the update by setting update_if_duplicate to False (default: True).

        Override self.get_cache_key to implement a different approach to turning `querydict` arg into hashable key.

        Keywords:
           update_if_duplicate: (bool) see note above.

        :param querydict: serializable
        :param value: serializable value
        :return: True if successful
        :raises: MySQLdb exceptions and json serialization errors
        """
        cvalue = self.get_cache_value(value)
        fv_dict = {'cache_key': self.get_cache_key(querydict), 'cache_value': cvalue, 'version': self.VERSION}

        try:
            self.insert(self.tablename, fv_dict)
        except mdb.IntegrityError:
            if kwargs.get('update_if_duplicate', True):
                # update entry with current time
                return self.update(fv_dict)
            else:
                return False

        return True

    def delete(self, querydict):
        sql = 'delete from {db.tablename} where cache_key="{key}"'.format(db=self, key=self.get_cache_key(querydict))
        self.execute(sql)

    def retrieve(self, querydict, version=0):
        """ If cache contains a value for this querydict, return it. Otherwise, return None.

        If requested version number is GREATER THAN OR EQUAL TO version number of existing data, older version will be
        destroyed so that newer version can be created in its place.

        Thus, supplying version=0 allows returns from cache from *any* version of data that has ever been stored.

        :param querydict:
        :param version: (int) only return results from cache with greater than or equal version number [default: 0]
        :return: value at this cache location, or None
        """
        row = self.get_row(querydict)
        if row:
            if row['version'] >= version:
                return json.loads(row['cache_value'].decode('string_escape'))
            else:
                log.debug('Expiring obsolete entry at cache_key location %s.', self.get_cache_key(querydict))
                self.delete(querydict)
        return None

    def get_row(self, querydict):
        """ If cache contains a value for this querydict, return entire row (as dict). Otherwise, return None.

        :param querydict:
        :return: dictionary representing entire row for this query dictionary
        """
        key = self.get_cache_key(querydict)
        sql = 'SELECT * from ' + self.tablename + ' where cache_key = %s limit 1'
        return self.fetchrow(sql, key)

    def _create_triggers(self):
        sql = """create trigger `{db.tablename}_new_entry_date` before INSERT on `{db.tablename}`
                for each row set new.date_created = now()""".format(db=self)
        self.execute(sql)

        sql = """create trigger `{db.tablename}_update` before UPDATE on `{db.tablename}`
                for each row set new.date_created = now()""".format(db=self)
        self.execute(sql)

    def create_table(self, reset=False):
        if reset:
            self.execute("DROP TABLE IF EXISTS {}".format(self.tablename))

        sql = """CREATE TABLE {} (
                cache_key varchar(255) primary key not null,
                cache_value text default NULL,
                date_created datetime default NULL,
                version int(11) default 0
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(self.tablename)

        try:
            self.execute(sql)
            self._create_triggers()
            return True
        except mdb.OperationalError as error:
            if error.args[0] == 1050:
                # if table already exists, we're fine.
                return True

            raise mdb.OperationalError(error.args)

    def drop_table(self):
        super(SQLCache, self).drop_table(self.tablename)

    def reset(self, before=None):
        # UNTESTED!
        # TODO: test:

        sql = "DELETE FROM {db.tablename} where date_created < ".format(db=self)

        if before:
            before = SQLdatetime(before)
        else:
            before = SQLdatetime(datetime.now())

        sql += '"%s"' % before

        self.execute(sql)

    def size(self):
        """ Counts number of rows currently in table.

        :return: (long) length of table in number of rows
        """
        result = self.execute("SELECT count(*) as cnt from {db.tablename}".format(db=self))
        return result.record[0]['cnt']
