from __future__ import print_function, absolute_import

from flask import Blueprint, render_template, redirect, request

from medgen.api import GeneID
from metapub import PubMedFetcher

from hgvs_lexicon import HgvsComponents
from hgvs_lexicon.exceptions import CriticalHgvsError

from .utils import HTTP200, get_hostname
from .config import ENV, CONFIG, PKGNAME

from .googlequery import GoogleQuery
from .exceptions import NCBIRemoteError
from .ncbi import LVGEnriched, NCBIHgvs2Pmid, NCBIReport, NCBIHgvsLVG
from .api import ClinvarHgvs2Pmid, PubtatorHgvs2Pmid
from .report_utils import (hgvs_to_clinvar_variationID, get_variation_url, get_lovd_url,
                           get_clinvar_tables_containing_variant)
from .report_utils import GeneInfo

fetch = PubMedFetcher()

base = Blueprint('base', __name__, template_folder='templates')

HGVS_SAMPLES = ['NM_194248.1:c.158C>T',
                'NM_014855.2:c.333G>C',
                'NM_001126115.1:c.318T>G',
                'NM_005228.3:c.2240_2257del18'
                ]


@base.route('/')
def home():
    return render_template('home.html') 


@base.route('/about')
def about():
    return render_template('about.html')


@base.route('/query', methods=['POST'])
@base.route('/query/<hgvs_text>', methods=['GET'])
def query(hgvs_text=''):
    """ Runs all of the relevant search queries after producing a lex object from input hgvs_text """

    if request.method == 'POST':
        hgvs_text = request.form.get('hgvs_text', '').strip()
        return redirect('/query/%s' % hgvs_text, code=302)
    else:
        hgvs_text = hgvs_text.strip()

    try:
        lex = LVGEnriched(hgvs_text)
    except CriticalHgvsError as error:
        return render_template('home.html', error_msg='%r' % error)

    if lex.gene_name:
        gene_info = GeneInfo(gene_name=lex.gene_name)
    else:
        gene_info = None

    variants = {'c': lex.hgvs_c,
                'g': lex.hgvs_g,
                'p': lex.hgvs_p,
                'n': lex.hgvs_n
                }

    clinvar_varID = hgvs_to_clinvar_variationID(hgvs_text)

    clinvar_results = {'pmids': ClinvarHgvs2Pmid(lex),
                       'variationID': hgvs_to_clinvar_variationID(hgvs_text),
                       'url': get_variation_url(clinvar_varID) if clinvar_varID else ''}

    pubtator_results = {'pmids': PubtatorHgvs2Pmid(lex)}

    ncbi_variants = []
    ncbi_results = {'pmids': [], 'report': None}

    try:
        ncbi_results = {'pmids': NCBIHgvs2Pmid(hgvs_text),
                        'report': NCBIReport(hgvs_text)}
        ncbi_lvg = NCBIHgvsLVG(hgvs_text)
        for seqtype in ncbi_lvg.variants:
            ncbi_variants = ncbi_variants + ncbi_lvg.variants[seqtype].keys()
    except NCBIRemoteError:
        pass

    comp = HgvsComponents(lex.seqvar)
    lovd_url = get_lovd_url(lex.gene_name, comp.pos)

    google_query = GoogleQuery(lex).build_query()

    return render_template('query.html', hgvs_text=hgvs_text, variants=variants, ncbi=ncbi_results,
                           clinvar=clinvar_results, pubtator=pubtator_results, lovd_url=lovd_url,
                           gene_name=lex.gene_name, ncbi_variants=ncbi_variants, gene_info=gene_info,
                           found_in_clinvar_example_tables=get_clinvar_tables_containing_variant(hgvs_text),
                           google_query=google_query)


@base.route('/examples')
def examples():
    api_version = CONFIG.get('api', 'latest_version')
    return render_template('examples.html', hgvs_samples=HGVS_SAMPLES, api_version=api_version)


@base.route('/OK')
def OK():
    return HTTP200({ 'service': '%s' % PKGNAME, 
                     'ENV': '%s' % ENV,
                     'hostname': '%s' % get_hostname(),
                     'api_latest_version': CONFIG.get('api', 'latest_version'), 
                     'api_supported_versions': CONFIG.get('api', 'supported_versions'),
                   })
