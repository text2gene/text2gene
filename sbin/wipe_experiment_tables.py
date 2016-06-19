from __future__ import print_function

import sys

from text2gene.sqlcache import SQLCache

PROMPT = '[n] > '

try:
    tname_pattern = sys.argv[1]
except IndexError:
    print('Supply pattern string to search-and-destroy MySQL tables. (e.g. "uncited_%")')
    sys.exit()

db = SQLCache('experiment')

#sql = "select TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA = DATABASE() and TABLE_NAME LIKE '{}'".format(tname_pattern)
sql = 'select TABLE_NAME from information_schema.TABLES where TABLE_NAME LIKE "{}"'.format(tname_pattern)
print(sql)

results = db.fetchall(sql)
tables = []

if not results:
    print()
    print('No tables matched pattern "%s"' % tname_pattern)
    print()
    sys.exit()

for row in results:
    tables.append(row['TABLE_NAME'])
    print('*', row['TABLE_NAME'])

print('WARNING: you are about to destroy the above tables. Go ahead???')
reply = raw_input(PROMPT)

if 'y' in reply.lower():
    print()
    print('ok, deleting...')
    for tname in tables:
        print('--', tname)
        db.execute('drop table %s' % tname)
    
else:
    print()
    print('ok, aborting!')
    print()

