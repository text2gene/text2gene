from __future__ import absolute_import, unicode_literals

API_INDICATOR = 'v1'

import logging

from flask import Blueprint, request, redirect

from metavariant.exceptions import CriticalHgvsError
from metavariant.utils import strip_gene_name_from_hgvs_text
from metavariant.lovd import LOVDVariantsForGene

from ..googlequery import GoogleQuery, GoogleCSEngine, googlecse2pmid, ALL_SEQTYPES, get_posedits_for_seqvar
from ..report_utils import CitationTable
from ..sqlcache import SQLCache
from ..ncbi import NCBIHgvs2Pmid, NCBIReport, LVGEnriched
from ..cached import PubtatorHgvs2Pmid, ClinvarHgvs2Pmid
from ..config import PKGNAME
from ..utils import HTTP200, HTTP400, restrict_by_ip

routes_v1 = Blueprint('routes_v1', __name__, template_folder='templates')

log = logging.getLogger('%s.routes_v1' % PKGNAME)


@routes_v1.route('/v1/hgvs2pmid/<hgvs_text>')
def hgvs2pmid(hgvs_text):
    """ Takes an input hgvs_text and uses a combination of methods to name pubmed
    articles by their PMID that mention this genetic variant.

        # a weird one:
        #NM_194248.1:c.158C>T

    :param hgvs_text: str
    :return: HTTP200 (json) or HTTP400 (json)
    """
    outd = {'action': 'hgvs2pmid', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        hgvs_text = strip_gene_name_from_hgvs_text(hgvs_text)
        try:
            lex = LVGEnriched(hgvs_text)
        except CriticalHgvsError as error:
            return HTTP400(error, 'Cannot parse input string %s as hgvs text' % hgvs_text)

        outd['lvg'] = lex.to_dict()

        outd['response'] = {}

        ncbi_pmids = NCBIHgvs2Pmid(lex.hgvs_text)
        if ncbi_pmids:
            outd['response']['ncbi'] = ncbi_pmids

        clinvar_pmids = ClinvarHgvs2Pmid(lex)
        if clinvar_pmids:
            outd['response']['clinvar'] = clinvar_pmids

        pubtator_pmids = PubtatorHgvs2Pmid(lex)
        if pubtator_pmids:
            outd['response']['abstracts'] = pubtator_pmids

    return HTTP200(outd)


@routes_v1.route('/v1/report/<hgvs_text>')
def ncbi_variant_reporter(hgvs_text):
    """ Takes an input hgvs_text and uses NCBI Variant Reporter to retrieve and display
    data related to this genetic variant.

    :param hgvs_text: str
    :return: HTTP200 (json) or HTTP400 (json)
    """
    outd = {'action': 'report', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        hgvs_text = strip_gene_name_from_hgvs_text(hgvs_text)
        report = NCBIReport(hgvs_text)

        outd['response'] = report

    return HTTP200(outd)


@routes_v1.route('/v1/lvgenriched/<hgvs_text>')
def lvg_enriched(hgvs_text):
    """ Takes an input hgvs_text and generates valid HGVS alternative statements,
    using a pre-enrichment process of seeding VariantLVG with variants from the NCBI Variation Reporter.

    Returns JSON (http 200).  If problem w/ HGVS string, responds with http 400
    """

    outd = {'action': 'lvgenriched', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        hgvs_text = strip_gene_name_from_hgvs_text(hgvs_text)
        try:
            hgvs_obj = LVGEnriched(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error using VariantLVG to find lexical variants for %s' % hgvs_text)
        outd['response'] = hgvs_obj.to_dict()

    return HTTP200(outd)


@routes_v1.route('/v1/lvg/<hgvs_text>')
def lvg(hgvs_text):
    """ Takes an input hgvs_text and generates valid HGVS alternative statements. 
        Returns JSON (http 200).  If problem w/ HGVS string, responds with http 400
    """

    outd = {'action': 'lvg', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        hgvs_text = strip_gene_name_from_hgvs_text(hgvs_text)
        try:
            lex = LVGEnriched(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error using LVGEnriched to find lexical variants for %s' % hgvs_text)

        outd['response'] = lex.to_dict()
        outd['response']['synonyms'] = {}

        for seqvar in lex.seqvars:
            outd['response']['synonyms']['%s' % seqvar] = get_posedits_for_seqvar(seqvar)

    return HTTP200(outd)


@routes_v1.route('/v1/google', methods=['POST'])
@routes_v1.route('/v1/google/<hgvs_text>', methods=['GET'])
@restrict_by_ip
def google_query(hgvs_text='<hgvs_text>', **kwargs):
    """ Performs LVG and GoogleQuery for given hgvs_text string.

    Available keywords:
            cse: 'whitelist' or 'schema'
            seqtypes: any combination of c,p,g,n (comma-separated list)

    :return: json including text of built query and structured data of Google response
    """

    if request.method == 'POST':
        hgvs_text = request.form.get('hgvs_text')
        seqtypes = request.form.getlist('seqtypes')
        cse = request.form.get('cse')
        log.debug('POST form contained: hgvs_text=%s, seqtypes=%s, cse=%s' % (hgvs_text, ','.join(seqtypes), cse))
        return redirect(
            '/v1/google/%s?seqtypes=%s&cse=%s' % (hgvs_text, ','.join(seqtypes), cse), code=302)

    else:
        hgvs_text = hgvs_text.strip()
        seqtypes = request.args.get('seqtypes', ','.join(ALL_SEQTYPES)).split(',')
        cse = request.args.get('cse', 'whitelist')

    outd = {'action': 'google', 'hgvs_text': hgvs_text, 'cse': cse,
            'seqtypes': seqtypes,
            'query': '',
            'pmids': '',
            'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        hgvs_text = strip_gene_name_from_hgvs_text(hgvs_text)
        try:
            lex = LVGEnriched(hgvs_text)
        except Exception as error:
            return HTTP400(error, 'Error before building query: could not build LVG object for %s.' % hgvs_text)

        outd['query'] = GoogleCSEngine(lex).build_query(seqtypes)

        cse_results = GoogleQuery(lex, seqtypes=seqtypes)

        outd['pmids'] = googlecse2pmid(cse_results)
        outd['response'] = []
        for res in cse_results:
            outd['response'].append(res.to_dict())

    return HTTP200(outd)


@routes_v1.route('/v1/citation_table/<hgvs_text>', methods=['GET'])
@restrict_by_ip
def citation_table(hgvs_text):
    """ Returns JSON containing hgvs2pmid, googlequery, and lvg characteristics for given hgvs_text """
    hgvs_text = hgvs_text.strip()
    outd = {'action': 'citation_table', 'hgvs_text': hgvs_text, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if 'hgvs_text' not in hgvs_text:
        try:
            lex = LVGEnriched(hgvs_text)
            ctable = CitationTable(lex)
            outd['response'] = ctable.to_dict()
        except Exception as error:
            return HTTP400(error, 'CitationTable failed for %s' % hgvs_text)

    return HTTP200(outd)


@routes_v1.route('/v1/cache_stats', methods=['GET'])
def cache_stats():
    """ Returns JSON containing statistics for the latest cache contents in MySQL. """
    db = SQLCache('clinvar')
    cache_report = {'ncbi_enriched_lvg_cache': None,
                    'google_query_cache': None,
                    'ncbi_report_cache': None,
                    'pubtator_hgvs2pmid_cache': None,
                    'clinvar_hgvs2pmid_cache': None,
                    'ncbi_hgvs2pmid_cache': None,
                    }
    for tablename in list(cache_report.keys()):
        result = db.fetchrow('select count(cache_key) as cnt from ' + tablename)
        cache_report[tablename] = result['cnt']

    return HTTP200(cache_report)


@routes_v1.route('/v1/experiment/<name>', methods=['GET'])
def experiment(name):
    """ Returns JSON containing experiment results (in progress or completed) for given experiment name. """
    db = SQLCache('experiment')
    name = name.strip()
    outd = {'action': 'experiment', 'name': name, 'response': 'Change <hgvs_text> in url to HGVS string.'}

    if name != '<name>':
        tname_pattern = name + '%'
        sql = 'select TABLE_NAME from information_schema.TABLES where TABLE_NAME LIKE "%s"' % tname_pattern
        rows = db.fetchall(sql)
        if not rows:
            outd['response'] = 'No tables matched pattern "%s"' % tname_pattern
        else:
            tables = {}
            for row in rows:
                tablename = row['TABLE_NAME']
                sql = 'select count(*) as cnt from %s' % tablename
                res = db.fetchrow(sql)
                tables[tablename] = res['cnt']
            outd['response'] = tables

    return HTTP200(outd)


@routes_v1.route('/v1/lovd_variants_for_gene/<symbol>', methods=['GET'])
def lovd_variants_for_gene(symbol):
    """ Returns JSON containing variant list retrieved from LOVD (lovd.nl) for given Hugo gene symbol """

    symbol = symbol.strip()
    outd = {'action': 'lovd_variants_for_gene', 'symbol': symbol, 'response': 'Change <symbol> in url to Hugo gene symbol'}
    if 'symbol' not in symbol:
        try:
            outd['response'] = list(LOVDVariantsForGene(symbol))
        except Exception as error:
            HTTP400(error)

    return HTTP200(outd)
