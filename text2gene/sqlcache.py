from __future__ import absolute_import, unicode_literals

import hashlib

import medgen.config as medgen_config

from pubtatordb import SQLData


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


    @staticmethod
    def make_cache_key(self, querydict):
        """ Default method to make a unique cache key from an input dictionary.
        """
        return hashlib.md5(pickle.dumps((url, sorted(querydict.items())))).hexdigest()

    def store(self, querydict, value):
        date_created = kwargs.get('date_created', datetime.now())
        fv_dict = {'cache_key': self.make_cache_key(querydict), 'cache_value': value, 'date_created': date_created}
        self.insert(self.tablename, fv_dict)

    def retrieve(self, querydict):
        """ If cache contains a value for this querydict, return it. Otherwise, return None.

        :param querydict:
        :return: value at this cache location, or None
        """
        with row as self.get_row(querydict):
            return row['cache_value']
        return None

    def get_row(self, querydict):
        """ If cache contains a value for this querydict, return entire row (as dict). Otherwise, return None.

        :param querydict:
        :return: dictionary representing entire row for this query dictionary
        """
        key = self.make_cache_key(querydict)
        sql = 'SELECT * from {db.tablename} where cache_key = "{key}" limit 1'.format(db=self, key=key)
        return self.fetchrow(sql)

    #def table_exists(self):
    #    sql =

    def create_table(self):

        sql = """CREATE TABLE {} (
                cache_key varchar(255) primary key not null,
                cache_value text default NULL,
                date_created datetime default NULL,
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci""".format(self.tablename)

        self.execute(sql)
