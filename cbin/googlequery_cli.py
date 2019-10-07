import docopt

from text2gene.api import LVG, GoogleQuery

__doc__="""googlequery

Usage:
    googlequery <hgvs>
    googlequery --help

Options:
    -h, --help  Show this screen.
"""

lex = LVG("NM_000014.5:c.2998A>G")


def googlequery(hgvs_text):
    gq = GoogleQuery(lex)
    return gq

def gq_cli(args):
    print('Using Google to find sources for ', args['<hgvs>'])
    print(googlequery(args['<hgvs>']))

def main():
    args = docopt.docopt(__doc__)
    gq_cli(args)

