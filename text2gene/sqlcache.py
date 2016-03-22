from __future__ import absolute_import, unicode_literals

import hashlib
import pickle
import json
from datetime import datetime

import MySQLdb as mdb

from medgen.config import config as medgen_config

from pubtatordb.sqldata import SQLData, SQLdatetime


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

    def update(self, fv_dict):
        """
        :param fv_dict: field-value dictionary with values intended to replace existing entry at cache_key
        :return: True if successful
        :raises: MySQLdb exceptions
        """
        sql = "update {db.tablename} set cache_value='{cache_value}' where cache_key='{cache_key}'".format(db=self, **fv_dict)
        self.execute(sql)
        return True

    def store(self, querydict, value, **kwargs):
        """ Takes a query dictionary containing "defining arguments" for the resultant value to be cached and the value,
        stores this as cache_key - cache_value in the cache DB.

        The value MUST be serializable to a string. (json.dumps will be used)

        If an entry with previously stored querydict exists, entry will be updated with date_created set to datetime.now()
        This behavior can be changed to ignoring the update by setting update_if_duplicate to False (default: True).

        Keywords:
           update_if_duplicate: (bool) see note above.

        :param querydict:
        :param value: serializable value
        :return: True if successful
        :raises: MySQLdb exceptions and json serialization errors
        """
        fv_dict = {'cache_key': self.get_cache_key(querydict), 'cache_value': json.dumps(value) }

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
        sql = 'delete from {db.tablename} where cache_key={key}'.format(db=self, key=self.get_cache_key(querydict))
        self.execute(sql)

    def retrieve(self, querydict):
        """ If cache contains a value for this querydict, return it. Otherwise, return None.

        :param querydict:
        :return: value at this cache location, or None
        """
        row = self.get_row(querydict)
        if row:
            return json.loads(row['cache_value'])
        return None

    def get_row(self, querydict):
        """ If cache contains a value for this querydict, return entire row (as dict). Otherwise, return None.

        :param querydict:
        :return: dictionary representing entire row for this query dictionary
        """
        key = self.get_cache_key(querydict)
        sql = 'SELECT * from {db.tablename} where cache_key = "{key}" limit 1'.format(db=self, key=key)
        return self.fetchrow(sql)

    def _create_triggers(self):
        sql = """create trigger `{db.tablename}_new_entry_date` before INSERT on `{db.tablename}`
                for each row set new.date_created = now()""".format(db=self)
        self.execute(sql)

        sql = """create trigger `{db.tablename}_update` before UPDATE on `{db.tablename}`
                for each row set new.date_created = now()""".format(db=self)
        self.execute(sql)

    def create_table(self):

        sql = """CREATE TABLE {} (
                cache_key varchar(255) primary key not null,
                cache_value text default NULL,
                date_created datetime default NULL
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

        sql += before

        self.execute(sql)
