from __future__ import absolute_import, print_function

""" This script retrieves a list of all HUMAN genes found via the Monarch API for a given search term. """

import sys

import requests

json_endpoint = 'https://monarchinitiative.org/search/{}.json'

try:
    term = sys.argv[1]
except IndexError:
    print("supply a search term enclosed in quotes as argument to this script.")
    sys.exit()


response = requests.get(json_endpoint.format(term))
if not response.ok:
    print(response.status_code)
    print(response.content)
    sys.exit()

genes = set()

results = response.json()['results']
for res in results:
    if 'gene' in res['categories']:
        if 'Human' in res['taxon']:
            genes.add(res['labels'][0])

print(' '.join(list(genes)))

