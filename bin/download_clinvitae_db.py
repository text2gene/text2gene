from __future__ import absolute_import, print_function

import os, sys
import csv
import logging

from medgen.api import ClinvarVariationID
from text2gene import LVGEnriched
from metavariant.exceptions import CriticalHgvsError, RejectedSeqVar
from metavariant import VariantComponents

CLINVITAE_DOWNLOAD_LINK = 'http://clinvitae.invitae.com/download'

log = logging.getLogger('script')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('./logs/variant_comparison.log')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)
logging.getLogger('text2gene').addHandler(fh)

try:
    tsvfile = open('data_nocommit/variant_results.tsv')
except Exception as error:
    print(error)
    print()
    print('Oops!  First you gotta download the ClinVitae database and extract it into the "data_nocommit" directory.')
    print('Rerun this script when you do!')
    print()
    print('ClinVitae download link: %s' % CLINVITAE_DOWNLOAD_LINK)
    print()

# One TSV row as dictionary:
#
# {'Gene\tNucleotide Change\tProtein Change\tOther Mappings\tAlias\tTranscripts\tRegion\tReported Classification\tInferred Classification\tSource\tLast Evaluated\tLast Updated\tURL\tSubmitter Comment\t': 'BCKDHA\tNM_000709.3:c.975C>T\tp.(=)\tNM_000709.3:c.975C>T\tNM_000709.2:c.975C>T | NM_000709.3:c.975C>T | NM_001164783.1:c.972C>T | NM_198540.2:c.*2835G>A', None: ['RCV000079267\tNM_000709.3\tEx7\tBenign\tBenign\tEmvClass\t2014-03-04\t2015-05-29\thttp://genetics.emory.edu/egl/emvclass/emvclass.php?approved_symbol=BCKDHA\t']}

def find_variant_in_clinvar(lex):
    for seqvar in lex.seqvars:
        try:
            comp = VariantComponents(seqvar)
            if ClinvarVariationID('%s' % seqvar):
                return seqvar
        except RejectedSeqVar:
            pass

    return None

empty = 0
unparseable = 0
in_clinvar = 0
not_in_clinvar = 0
count = 0
errors = 0

reader = csv.DictReader(tsvfile, delimiter='\t')

for row in reader:
    count += 1
    hgvs_text = row['Nucleotide Change'].strip().replace(' ', '')
    log.debug(hgvs_text)
    if hgvs_text.replace('-', '') == '':
        empty += 1
        continue

    try:
        lex = LVGEnriched(hgvs_text)
        seqvar_in_clinvar = find_variant_in_clinvar(lex)
        if seqvar_in_clinvar:
            print(count, hgvs_text, 'in clinvar as %s' % seqvar_in_clinvar)
            log.info('%s in clinvar as %s', hgvs_text, seqvar_in_clinvar)
            in_clinvar += 1
        else:
            not_in_clinvar += 1
            print(count, hgvs_text, 'NOT in clinvar')
            log.info('%s NOT in clinvar', hgvs_text)

    except CriticalHgvsError as error:
        unparseable += 1
        print('%i %s unparseable' % (count, hgvs_text))
        log.info('%s unparseable', hgvs_text)
        continue
    except Exception as error:
        errors += 1
        print('%s ERROR: %r' % (hgvs_text, error))
        log.info('%s ERROR', hgvs_text, error)
        continue

print('==================')
print('Empty: %i' % empty)
print('Unparseable: %i' % unparseable)
print('IN Clinvar: %i' % in_clinvar)
print('NOT in Clinvar: %i' % not_in_clinvar)
print('Errors: %i' % errors)
print()
print('Total counted: %i' % count)
print()
print('Sanity check: %i' % (empty + unparseable + in_clinvar + not_in_clinvar + errors))
print('(Done)')


