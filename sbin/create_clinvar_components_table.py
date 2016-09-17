from __future__ import absolute_import, print_function

from metavariant import Variant, VariantComponents
from metavariant.exceptions import RejectedSeqVar, CriticalHgvsError
from medgen.db.clinvar import ClinVarDB

from text2gene.api import LVGEnriched

from pubtatordb.sqldata import SQLData
from pubtatordb.config import get_process_log

log = get_process_log('logs/clinvar_components_table.log')


ERRORS = 0
GOOD = 0

DB_ERROR_FILE = open('logs/clinvar_components_db_errors.txt', 'w')

def write_db_error(msg, err_obj):
    DB_ERROR_FILE.write('%r: %s\n' % (err_obj, msg))
    DB_ERROR_FILE.flush()

def components_or_None(hgvs_p):
    try:
        comp = VariantComponents(Variant(hgvs_p))
        if comp.ref != '':
            return comp
    except (TypeError, RejectedSeqVar, CriticalHgvsError):
        # either the hgvs_p did not parse (Variant returned None) or it has incomplete edit info.
        pass
    return None


def process_row(dbrow):

    # first try the HGVS_p (preferred)
    comp = components_or_None(dbrow['HGVS_p'])
    if comp:
        return comp

    for option in ['variant_name', 'HGVS_c']:
        hgvs_text = dbrow[option].strip()
        if hgvs_text is None:
            continue

        # look out for variants in this format:  NM_001363.4(DKC1):c.1058C>T (p.Ala353Val)
        if (hgvs_text.split()) > 1:
            hgvs_text = hgvs_text.split()[0]

        # beware the pesky N-dash in at least 1 observed ClinVar db entry.
        hgvs_text = hgvs_text.replace('\u2013', '-')

        try:
            seqvar = Variant(hgvs_text)
        except (CriticalHgvsError, TypeError):
            # empty or broken
            continue

        if seqvar:
            try:
                lvg = LVGEnriched(seqvar)
            except Exception as error:
                write_db_error('Could not create LVGEnriched object for %s' % seqvar, error)
                log.debug('ERROR: %r' % error)
                log.info('Could not create LVGEnriched object for %s' % seqvar)
                return None

            for entry in lvg.hgvs_p:
                comp = components_or_None(entry)
                if comp and comp.ref:
                    return comp
    return None


def add_components_to_row(db, dbrow, comp):
    print('ADD:')
    try:
        print('\tRef:%s' % comp.ref)
        print('\tPos:%s' % comp.pos)
        print('\tAlt:%s' % comp.alt)

        db.execute('update variant_components set Ref=%s, Pos=%s, Alt=%s where variant_name=%s',
                        dbrow['Ref'], dbrow['Pos'], dbrow['Alt'], dbrow['variant_name'])

    except AttributeError as error:
        print(error)

    print()


def main():
    global ERRORS
    global GOOD

    db = ClinVarDB()
    log.info('Started "create_clinvar_components_table.py"')
    
    # hello, are you there MySQL? It's me, python.
    db.ping()

    try:
        res = db.fetchrow('select count(*) as cnt from variant_components')
    except Exception as error:
        print(error)
        log.debug('%r' % error)
        sys.exit()

    log.info('Rows in variant_components table: %i' % res['cnt'])

    rows = db.fetchall('select * from variant_components order by rand()')

    worked = 0
    errors = 0
    count = 0
    for row in rows:
        count += 1
        print(count, '/', res['cnt'], ':', row['variant_name'])
        components = process_row(row)
        if components:
            GOOD += 1
            print('[%s] added components: %r' % (row['variant_name'], components))
            add_components_to_row(db, row, components)
            log.info(row['variant_name'] + ' - no usable amino acid components')
        else:
            ERRORS += 1
            print('[%s] no usable amino acid components' % row['variant_name'])
            log.info(row['variant_name'] + ' - no usable amino acid components')
    
if __name__=='__main__':
    main()

    print('unusable:', ERRORS)
    print('good:', GOOD)

