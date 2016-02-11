from __future__ import absolute_import

from pyrfc3339 import parse

import MySQLdb as mdb
import MySQLdb.cursors as cursors
import PySQLPool

import logging

from .config import DATABASE, DEBUG

log = logging.getLogger()
if DEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.ERROR)

DEFAULT_HOST = DATABASE['host']
DEFAULT_USER = DATABASE['user']
DEFAULT_PASS = DATABASE['pass'] 
DEFAULT_NAME = DATABASE['name']


SQLDATE_FMT = '%Y-%m-%d %H:%M:%S'

def SQLdatetime(pydatetime_or_string):
    if hasattr(pydatetime_or_string, 'strftime'):
        dtobj = pydatetime_or_string
    else:
        # assume pyrfc3339 string
        dtobj = parse(pydatetime_or_string)
    return dtobj.strftime(SQLDATE_FMT)

class SQLData(object):
    """
    MySQL base class for config, select, insert, update, and delete in MySQL databases.
    """
    def __init__(self, *args, **kwargs):
        self._db_host = kwargs.get('host', None) or DEFAULT_HOST
        self._db_user = kwargs.get('user', None) or DEFAULT_USER
        self._db_pass = kwargs.get('pass', None) or DEFAULT_PASS
        self._db_name = kwargs.get('name', None) or DEFAULT_NAME

    def connect(self):
        return PySQLPool.getNewConnection(username=self._db_user, 
                password=self._db_pass, host=self._db_host, db=self._db_name)

    def cursor(self, execute_sql=None):
        conn = self.connect()
        cursor = conn.cursor(cursors.DictCursor)

        if execute_sql is not None:
            cursor.execute(execute_sql)

        return [conn, cursor]

    def fetchall(self, select_sql):
        try:
            return self.execute(select_sql).record
        #except mdb.Error as err:
        #    log.warn(err)
        #    return None
        except TypeError:
            # no results
            return None

    def fetchrow(self, select_sql):
        results = self.fetchall(select_sql)
        return results[0] if results else None

    def fetchID(self, select_sql, id_colname='ID'):
        try:
            return self.fetchrow(select_sql)[id_colname]
        except TypeError:
            return None

    def results2set(self, select_sql, col):
        things = set()
        for row in self.fetchall(select_sql):
            things.add(str(row[col]))
        return things

    def _get_fields_and_values(self, field_value_dict, None_as_null=True):
        """ Return a tuple containing (fields, values) in which the keys 
        of the dictionary become a list of field names, and the values of
        of the dictionary become a list of pre-quoted, mysql-escaped values.

        python datetime objects will be converted to SQL datetime strings.

        :param new_data: list of field:value dictionaries
        :param None_as_null: (bool)
        :returns: (list, list) containing (fields, values)
        """
        fields = []
        values = []

        for key, val in field_value_dict.items():
            if val==None and not None_as_null:
                continue
            fields.append(key)
            # surround strings and datetimes with quotation marks
            if hasattr(val, 'strftime'):
                val = '"%s"' % val.strftime(SQLDATE_FMT)
            elif hasattr(val, 'lower'):
                val = '"%s"' % mdb.escape_string(val)
            elif val is None:
                val = 'NULL'
            else:
                val = str(val)

            values.append(val)
        return fields, values

    def batch_insert(self, tablename, new_data):
        """ Insert new_data (list of dicts with identical schemas) into 
        indicated tablename.  

        Warning: supplied data MUST have identical data structure!

        :param tablename: name of table to receive new rows
        :param new_data: list of field:value dictionaries
        """
        # suss out the schema of the dictionaries.
        fields = new_data[0].keys()

        # store each set of values in a list
        all_values = []

        for field_value_dict in new_data:
            _, values = self._get_fields_and_values(field_value_dict)
            all_values.append('(%s)' % ','.join(values))

        sql = 'insert into %s (%s) values (%s);' % (tablename, ','.join(fields), ','.join(all_values))
        print(sql)

        queryobj = self.execute(sql)
        # # retrieve and return the row id of the insert. returns 0 if insert failed.
        # return queryobj.lastInsertID      # unclear what this would do. return a list?

    def insert(self, tablename, field_value_dict, None_as_null=False):
        """ Insert field_value_dict into indicated tablename.

        By default, fields with None values will *not* be added to the INSERT operation.
        Supply None_as_null=True to change this behavior.
         
        :param tablename: name of table to receive new row
        :param field_value_dict: map of field=value
        :param None_as_null: (bool) whether to insert None values as NULL [default: False]
        :return row_id: (integer) (returns 0 if insert failed)
        """
        fields, values = self._get_fields_and_values(field_value_dict, None_as_null=None_as_null)

        sql = 'insert into %s (%s) values (%s);' % (tablename, ','.join(fields), ','.join(values)) 
        queryobj = self.execute(sql)
        # retrieve and return the row id of the insert. returns 0 if insert failed.
        return queryobj.lastInsertID

    def drop_table(self, tablename):
        return self.execute(' drop table if exists ' + tablename)

    def truncate(self, tablename):
        return self.execute(" truncate " + tablename)

    def execute(self, sql):
        log.debug('SQL.execute ' + sql)
        log.debug('#######')
        queryobj = PySQLPool.getNewQuery(self.connect(), commitOnEnd=True)
        queryobj.Query(sql)
        return queryobj

    def ping(self):
        """
        Same effect as calling 'mysql> call mem'
        :returns::self.schema_info(()
        """
        try:
            return self.schema_info()

        except mdb.Error as err:
            log.error("DB connection is dead %d: %s" % (err.args[0], err.args[1]))
            return False

    def schema_info(self):
        header = ['schema', 'engine', 'table', 'rows', 'million', 'data length', 'MB', 'index']
        return {'header': header, 'tables': self.fetchall('call mem')}

