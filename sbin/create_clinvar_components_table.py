from __future__ import absolute_import, print_function

from metavariant import Variant, VariantComponents
from metavariant.exceptions import RejectedSeqVar
from medgen.db.clinvar import ClinVarDB

from text2gene.api import LVGEnriched

from pubtatordb.sqldata import SQLData
from pubtatordb.config import get_process_log

log = get_process_log('logs/clinvar_components_table.log')


ERRORS = 0
GOOD = 0


def components_or_None(hgvs_p):
    try:
        return VariantComponents(Variant(hgvs_p))
    except (TypeError, RejectedSeqVar):
        # either the hgvs_p did not parse (Variant returned None) or it has incomplete edit info.
        return None


def process_row(dbrow):

    # first try the HGVS_p (preferred)
    comp = components_or_None(dbrow['HGVS_p'])
    if comp:
        return comp

    for option in ['variant_name', 'HGVS_c']:
        # look out for variants in this format:  NM_001363.4(DKC1):c.1058C>T (p.Ala353Val)
        if (option.split()) > 1:
            option = option.split()[0]    

        try:
            seqvar = Variant(dbrow[option])
        except TypeError:
            # empty
            continue
        if seqvar:
            lvg = LVGEnriched(seqvar)
            for entry in lvg.hgvs_p:
                comp = components_or_None(entry)
                if comp:
                    return comp
    return None


def add_components_to_row(dbrow, comp):
    print('ADD:')
    try:
        print('\tRef:%s' % comp.ref)
        print('\tPos:%s' % comp.pos)
        print('\tAlt:%s' % comp.alt)
    except AttributeError as error:
        print(error)
        from IPython import embed; embed()

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

    rows = db.fetchall('select * from variant_components')

    worked = 0
    errors = 0
    count = 0
    for row in rows:
        count += 1
        print(count, '/', res['cnt'])
        components = process_row(row)
        if components:
            GOOD += 1
            print('[%s] added components: %r' % (row['variant_name'], components))
            add_components_to_row(row, components)
            log.info(row['variant_name'] + ' - no usable amino acid components')
        else:
            ERRORS += 1
            print('[%s] no usable amino acid components' % row['variant_name'])
            log.info(row['variant_name'] + ' - no usable amino acid components')
    
if __name__=='__main__':
    main()

    print('unusable:', ERRORS)
    print('good:', GOOD)

