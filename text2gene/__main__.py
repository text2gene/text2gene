from __future__ import absolute_import, print_function, unicode_literals

from docopt import docopt

from metapub import FindIt
from medgen.api import GeneID
from metavariant import VariantComponents, Variant
from metavariant.exceptions import RejectedSeqVar
from hgvs.exceptions import HGVSParseError

from aminosearch import PubtatorDB

from .cached import PubtatorHgvs2Pmid, ClinvarHgvs2Pmid
from .api import LVG, GoogleQuery


pubtator_db = PubtatorDB()

SQLDEBUG = True

__author__ = 'Naomi Most <naomi@text2gene.com>'
__version__ = '1.0'     # version of THIS cli app, hgvs2pmid
__doc__ = """hgvs2pmid

Usage:
    hgvs2pmid <hgvs>
    hgvs2pmid --help

Examples of HGVS strings you could try:

    NM_007294.3(BRCA1):c.2706delA
    NP_009225.1(BRCA1):p.Ser955Ter
    NP_009225.1:p.Ser955Ter

It will probably help to surround the HGVS string with quotation marks.

Options:
    -h, --help      Show this page.

"""


### Suppress warnings from biocommons and IPython
import warnings
warnings.simplefilter('ignore')
###

def print_article_for_pmid(pmid):
    try:
        source = FindIt(pmid, verify=False)
    except Exception as error:
        print("Something's wrong with Gilligan's Island... %s" % pmid)    
        return

    print('----- PMID: %s' % pmid)
    print(source.pma.title)
    if source.url:
        print(source.url)
    else:
        print(source.reason)


#######################################################################
# Mutation2Pubtator SeqTypes --> the higher count SeqTypes are higher priority. 
# Note that many SeqType are null, and therefore need to be implied!
# Amino Acids List
# List of the 20 protein (amino acids) 
# http://www.cryst.bbk.ac.uk/education/AminoAcid/the_twenty.html
# If SeqType is none and REF in [u] or ALT in [u] --> then RNA
# If SeqType is none and REF in [t] or ALT in [t] --> then DNA
# If SeqType is none and REF in [a,c,t,g] and ALT in [a,c,t,g] --> then DNA or RNA
# If SeqType is none and REF in [AminoAcidsList] and ALT in [AminoAcidsList] --> then Protein
#
# JIRA: https://text2gene.atlassian.net/browse/T2G-3


def hgvs_to_pmid_results_dict(hgvs_text):
    print()
    print('[%s]' % hgvs_text)

    lex = LVG(hgvs_text)

    edittype = VariantComponents(lex.seqvar).edittype
    if edittype not in ['SUB', 'DEL', 'INS', 'FS', 'INDEL']:
        print('[%s] Cannot process edit type %s; skipping' % (hgvs_text, edittype))
        return None

    try:
        gene_id = GeneID(lex.gene_name)
    except TypeError:
        # no gene_name? it happens.
        gene_id = None

    print('[%s]' % hgvs_text, lex.gene_name, '(Gene ID: %s)' % gene_id)

    pmid_results = {}
    pmid_results['PubTator'] = PubtatorHgvs2Pmid(lex)
    pmid_results['ClinVar'] = ClinvarHgvs2Pmid(lex)
    return pmid_results


def process_hgvs_through_pubtator(hgvs_text):
    print()
    print('[%s]' % hgvs_text)

    lex = LVG(hgvs_text)

    edittype = VariantComponents(lex.seqvar).edittype
    if edittype not in ['SUB', 'DEL', 'INS', 'FS', 'INDEL']:
        print('[%s] Cannot process edit type %s; skipping' % (hgvs_text, edittype))
        return None

    try:
        gene_id = GeneID(lex.gene_name)
    except TypeError:
        # no gene_name? it happens.
        gene_id = None

    print('[%s]' % hgvs_text, lex.gene_name, '(Gene ID: %s)' % gene_id)

    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype]:
            try:
                components = VariantComponents(seqvar)
            except RejectedSeqVar:
                print('[%s] Rejected sequence variant: %r' % (hgvs_text, seqvar))
                continue

            print('[%s]' % hgvs_text, seqtype, components)
            if seqtype == 'p':
                results = pubtator_db.search_proteins(components, gene_id)
            else:
                results = pubtator_db.search_m2p(components, gene_id)

            for res in results:
                pmids.add(res['PMID'])

    return pmids


#TODO: convert to docopt
def cli_pubtator_search_string():
    import sys
    try:
        hgvs_text = sys.argv[1]
    except IndexError:
        print('Supply hgvs text as argument to this script.')
        sys.exit()

    try:
        pmids = process_hgvs_through_pubtator(hgvs_text)
        if pmids:
            print('[%s] PMIDs Found: %r' % (hgvs_text, pmids))
            for pmid in pmids:
                print_article_for_pmid(pmid)
        else:
            print('[%s] No PMIDs found.' % hgvs_text)

    except HGVSParseError:
        print('[%s] Cannot parse as HGVS; skipping' % hgvs_text) 


#TODO: convert to docopt
def cli_pubtator_search_file():
    import sys
    try:
        textfile = sys.argv[1]
    except IndexError:
        print('Supply path to text file with HGVS strings (one per line) as argument to this script.')
        sys.exit()

    with open(textfile, 'r') as fh:
        for hgvs_text in fh.read().split('\n'):
            if not hgvs_text.strip():
                continue
            try:
                pmids = process_hgvs_through_pubtator(hgvs_text)
                if pmids:
                    print('[%s] PMIDs Found: %r' % (hgvs_text, pmids))
                    for pmid in pmids:
                        print_article_for_pmid(pmid)
                else:
                    print('[%s] No PMIDs found.' % hgvs_text)
            except HGVSParseError:
                print('[%s] Cannot parse as HGVS; skipping' % hgvs_text) 


def hgvs2pmid(hgvs_text):
    try:
        results = hgvs_to_pmid_results_dict(hgvs_text)
        for key, pmids in results.items():
            print('[%s] %i PMIDs Found in %s: %r' % (hgvs_text, len(pmids), key, pmids))

    except HGVSParseError:
        print('[%s] Cannot parse as HGVS; skipping' % hgvs_text)


#TODO: convert to docopt
def cli_hgvsfile2pmid():
    import sys
    try:
        textfile = sys.argv[1]
    except IndexError:
        print('Supply path to text file with HGVS strings (one per line) as argument to this script.')
        sys.exit()

    with open(textfile, 'r') as fh:
        for hgvs_text in fh.read().split('\n'):
            if not hgvs_text.strip():
                continue
            try:
                results = hgvs_to_pmid_results_dict(hgvs_text)
                for key, pmids in results.items():
                    print('[%s] %i PMIDs Found in %s: %r' % (hgvs_text, len(pmids), key, pmids))

            except HGVSParseError:
                print('[%s] Cannot parse as HGVS; skipping' % hgvs_text)


def hgvs2pmid_cli():
    args = docopt(__doc__, version=__version__)
    var = Variant(args['<hgvs>'])
    if var:
        hgvs2pmid(str(var))
    else:
        print('Supplied argument must be a valid HGVS string! See --help for examples.')
        #end

    #print(err)
    #print('Not sure what to do next; quitting.')
    #end


GOOGLEQUERY_CLI_DOC = """googlequery

Usage:
    googlequery <hgvs>
    googlequery --help

Options:
    -h, --help  Show this screen.
"""

def googlequery(hgvs_text):
    lex = LVG(hgvs_text)
    gq = GoogleQuery(lex)
    return gq

def googlequery_cli():
    args = docopt(GOOGLEQUERY_CLI_DOC)
    print('Using Google to find sources for ', args['<hgvs>'])
    gq = googlequery(args['<hgvs>'])
    print(gq)


"""
mysql> select distinct M.* from gene2pubtator G, m2p_SUB M where G.PMID = M.PMID and G.GeneID = 120892 and pos=6055 and Ref = 'G' and Alt = 'A' and SeqType='c'; 
+----------+----------------+-------------+---------+----------+------+------+------+
| PMID     | Components     | Mentions    | SeqType | EditType | Ref  | Pos  | Alt  |
+----------+----------------+-------------+---------+----------+------+------+------+
| 16758483 | c|SUB|G|6055|A | c.6055G>A   | c       | SUB      | G    | 6055 | A    |
| 17116211 | c|SUB|G|6055|A | c.6055G>A   | c       | SUB      | G    | 6055 | A    |
| 17222106 | c|SUB|G|6055|A | c.6055G > A | c       | SUB      | G    | 6055 | A    |
| 17235449 | c|SUB|G|6055|A | c.6055G>A   | c       | SUB      | G    | 6055 | A    |
| 18211709 | c|SUB|G|6055|A | c.6055G > A | c       | SUB      | G    | 6055 | A    |
| 26600626 | c|SUB|G|6055|A | c.6055 G>A  | c       | SUB      | G    | 6055 | A    |
+----------+----------------+-------------+---------+----------+------+------+------+
"""
