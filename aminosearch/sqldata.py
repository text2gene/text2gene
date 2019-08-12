import logging

from pyrfc3339 import parse
import MySQLdb
import MySQLdb.cursors as cursors

from .config import DATABASE, SQLDEBUG, get_data_log

log = get_data_log('sqldata.log')
if SQLDEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.ERROR)

DEFAULT_HOST = DATABASE['host']
DEFAULT_USER = DATABASE['user']
DEFAULT_PASS = DATABASE['pass'] 
DEFAULT_NAME = DATABASE['name']


SQLDATE_FMT = '%Y-%m-%d %H:%M:%S'

def EscapeString(value):
    "Ensures utf-8 encoding of values going into tables."
    return value.encode("utf-8")

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

        self.conn = None

    def connect(self):
        self.conn = MySQLdb.connect(passwd=self._db_pass,
                                    user=self._db_user,
                                    db=self._db_name,
                                    host=self._db_host,
                                    cursorclass=cursors.DictCursor,
                                    charset='utf8',
                                    use_unicode=True,
                                   )
        return self.conn

    def cursor(self, execute_sql=None):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor(cursors.DictCursor)

        if execute_sql is not None:
            cursor.execute(execute_sql)

        return cursor

    def fetchall(self, select_sql, *args):
        """ For submitted select_sql with interpolation strings meant to match
        with supplied *args, build and execute the statement and fetch all results.

        Results will be returned as a list of dictionaries.

        Example:
            DB.fetchall('select HGVS from clinvar where PMID="%s"', ('21129721',))

        :param select_sql: (str)
        :returns: results as list of dictionaries
        :rtype: list
        """
        # this line opens a cursor, executes, gets the data, and closes the cursor.
        if args:
            results = self.cursor(select_sql % args).fetchall()
        else:
            results = self.cursor(select_sql).fetchall()
            
        return results

    def fetchrow(self, select_sql, *args):
        """
        If the query was successful:
            if 1 or more rows was returned, returns the first one
            else returns None
        Else:
            raises Exception
        """
        res = self.fetchall(select_sql, *args)
        return res[0] if len(res) > 0 else Noneo

    def fetchID(self, select_sql, *args, **kwargs):
        id_colname = kwargs.get('id_colname', 'ID')
        try:
            return self.fetchrow(select_sql, *args)[id_colname]
        except TypeError:
            return None

    def results2set(self, select_sql, col, *args):
        things = set()
        for row in self.fetchall(select_sql, *args):
            things.add(str(row[col]))
        return things

    def _get_fields_and_values(self, field_value_dict, None_as_null=True, quote_values=False):
        """ Return a tuple containing (fields, values) in which the keys 
        of the dictionary become a list of field names, and the values of
        of the dictionary become a list of pre-quoted, mysql-escaped values.

        python datetime objects will be converted to SQL datetime strings.

        :param new_data: list of field:value dictionaries
        :param None_as_null: (bool)
        :param quote_values: whether to surround value fields with quotation marks.
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
                if quote_values:
                    val = '"%s"' % val.strftime(SQLDATE_FMT)
                else:
                    val = '%s' % val.strftime(SQLDATE_FMT)
            elif hasattr(val, 'lower'):
                if quote_values:
                    val = '"%s"' % EscapeString(val)
                else:
                    val = '%s' % EscapeString(val)
            elif val is None:
                val = 'NULL'
            else:
                val = str(val)

            values.append(val)
        return fields, values

    def batch_insert(self, tablename, new_data):
        """ Insert new_data (list of dicts with identical schemas) into 
        indicated tablename.  

        Note: supplied data dictionaries MUST have identical data structure.

        WARNING: this is *really* not SQL-injection-safe, so don't wrap 
                end-user interfaces around this method, OK?

        :param tablename: name of table to receive new rows
        :param new_data: list of field:value dictionaries
        """
        # suss out the schema of the dictionaries.
        fields = new_data[0].keys()

        # store each set of values in a list
        all_values = []

        for field_value_dict in new_data:
            _, values = self._get_fields_and_values(field_value_dict, quote_values=True)
            all_values.append('(%s)' % ','.join(values))

        sql = 'insert into '+tablename+' (%s) values %s' % (','.join(fields), ','.join(all_values))
        cursor = self.cursor(sql)
        #TODO: anything we can do with the cursor object to report on success?
        print(cursor)

    def insert(self, tablename, field_value_dict, None_as_null=False):
        """ Insert field_value_dict into indicated tablename.

        By default, fields with None values will *not* be added to the INSERT operation.
        Supply None_as_null=True to change this behavior.
         
        :param tablename: name of table to receive new row
        :param field_value_dict: map of field=value
        :param None_as_null: (bool) whether to insert None values as NULL [default: False]
        :return row_id: (integer) (returns 0 if insert failed)
        """
        fields, values = self._get_fields_and_values(field_value_dict, None_as_null=None_as_null, quote_values=False)

        sql = 'insert into %s (%s) values (%s)' % (tablename, ','.join(fields), ','.join(['%s' for _ in values]))

        #copied in from medgen. 
        cursor = self.execute(sql, *values)
        cursor.close()
        return self.conn.insert_id()

    def drop_table(self, tablename):
        return self.execute('drop table if exists ' + tablename)

    def truncate(self, tablename):
        return self.execute('truncate ' + tablename)

    def execute(self, sql, *args):
        """
        Executes arbitrary sql string in current database connection.
        Use this method's args for positional string interpolation into sql.

        :param sql: (str)
        :return: MySQLdb cursor object
        """
        log.debug('SQL.execute ' + sql, *args)

        try:
            cursor = self.cursor(sql % args)
            log.debug('SQL.execute ' + sql % args)
        except Exception as err:
            log.info('Medgen SQL ERROR: %r' % err)
            full_sql = sql % args
            log.info('Tripped on a piece of SQL: ' + full_sql)
        log.debug('#######')
        return cursor

    def ping(self):
        """
        Same effect as calling 'mysql> call mem'
        :returns::self.schema_info(()
        """
        try:
            return self.schema_info()

        except Exception as err:
            log.error('DB connection is dead %d: %s', err.args[0], err.args[1])
            return False

    def schema_info(self):
        header = ['schema', 'engine', 'table', 'rows', 'million', 'data length', 'MB', 'index']
        return {'header': header, 'tables': self.fetchall('call mem')}

