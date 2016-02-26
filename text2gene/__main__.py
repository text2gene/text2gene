from __future__ import absolute_import, print_function, unicode_literals

from medgen.api import GeneID
from hgvs.exceptions import HGVSParseError
from metapub import FindIt

from pubtatordb import PubtatorDB
from hgvs_lexicon import HgvsLVG, HgvsComponents, RejectedSeqVar

pubtator_db = PubtatorDB()

SQLDEBUG = True


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
# If SeqType is none and REF in [a,c,t,g] and ALT in [a,c,t,g] --> then DNA or RNA 
# If SeqType is none and REF in [u] or ALT in [u] --> then DNA or RNA 
# If SeqType is none and REF in [AminoAcidsList] and ALT in [AminoAcidsList] --> then Protein
#
# JIRA: https://text2gene.atlassian.net/browse/T2G-3

def pubtator_search(comp, gene_id):
    #sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos={comp.pos} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and SeqType='{comp.seqtype}'".format(comp=comp, gene_id=gene_id)
    sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Ref = '{comp.ref}' and Alt = '{comp.alt}' and Pos='{comp.pos}'".format(comp=comp, gene_id=gene_id)
    if SQLDEBUG:
        print(' ---', sql)
    return pubtator_db.fetchall(sql)

def pubtator_search_by_protein(comp, gene_id):
    sql = "select distinct M.* from gene2pubtator G, m2p_{comp.edittype} M where G.PMID = M.PMID and G.GeneID = {gene_id} and Pos = '{comp.pos}' and SeqType='p' and Ref = '{comp.ref}'".format(comp=comp, gene_id=gene_id)
    if SQLDEBUG:
        print(' ---', sql)
    return pubtator_db.fetchall(sql)


def process_hgvs_text(hgvs_text):
    lex = HgvsLVG(hgvs_text)

    print()
    print('[%s]' % hgvs_text, lex)

    edittype = lex.seqvar.posedit.edit.type.upper()
    if edittype not in ['SUB', 'DEL', 'INS', 'FS', 'INDEL']:
        print('[%s] Cannot process edit type %s; skipping' % (hgvs_text, edittype))
        return None

    gene_id = GeneID(lex.gene_name)
    print('[%s]' % hgvs_text, lex.gene_name, '(Gene ID: %s)' % gene_id)

    pmids = set()
    for seqtype in lex.variants:
        for seqvar in lex.variants[seqtype]:
            try:
                components = HgvsComponents(seqvar)
            except RejectedSeqVar:
                print('[%s] Rejected sequence variant: %r' % (hgvs_text, seqvar))
                continue

            print('[%s]' % hgvs_text, seqtype, components)
            if seqtype == 'p':
                results = pubtator_search_by_protein(components, gene_id)
            else:
                results = pubtator_search(components, gene_id)
            for res in results:
                pmids.add(res['PMID'])

    return pmids


def process_one_from_command_line():
    import sys
    try:
        hgvs_text = sys.argv[1]
    except IndexError:
        print('Supply hgvs text as argument to this script.')
        sys.exit()

    try:
        pmids = process_hgvs_text(hgvs_text)
        if pmids:
            print('[%s] PMIDs Found: %r' % (hgvs_text, pmids))
            for pmid in pmids:
                print_article_for_pmid(pmid)
        else:
            print('[%s] No PMIDs found.' % hgvs_text)

    except HGVSParseError:
        print('[%s] Cannot parse as HGVS; skipping' % hgvs_text) 


def process_many_from_command_line():
    import sys
    try:
        textfile = sys.argv[1]
    except IndexError:
        print('Supply path to text file with HGVS strings (one per line) as argument to this script.')
        sys.exit()

    with open(textfile, 'r') as fh:
        for hgvs_text in fh.read().split('\n'):
            try:
                pmids = process_hgvs_text(hgvs_text)
                if pmids:
                    print('[%s] PMIDs Found: %r' % (hgvs_text, pmids))
                    for pmid in pmids:
                        print_article_for_pmid(pmid)
                else:
                    print('[%s] No PMIDs found.' % hgvs_text)
            except HGVSParseError:
                print('[%s] Cannot parse as HGVS; skipping' % hgvs_text) 


if __name__=='__main__':
    process_many_from_command_line()


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
