"""Loads data about all wares."""

from lxml import etree
from misc import get_xpath_attribs, get_xpath_attrib, get_path_in_ext


def ware_loader(floader, lresolver, ext_name):
    """Loads and parses wares and returns a ware_id -> ware_props dict.
    Ware properties is a dictionary.

    Arguments:
    floader: file loader.
    lresolver: language resolver.
    ext_name: extension to load wares from. Use None for the base game.
    """
    wares = {}

    wares_xml_path = get_path_in_ext('libraries/wares.xml', ext_name)

    with floader.open_file(wares_xml_path) as wares_file:
        tree = etree.parse(wares_file)

    for ware in tree.xpath('./ware'):
        props = {}

        ware_id = ware.get('id')
        props['name'] = lresolver.resolve_string(ware.get('name'), strip=True)
        props['description'] = \
            lresolver.resolve_string(ware.get('description'), strip=True)
        props['factoryname'] = \
            lresolver.resolve_string(ware.get('factoryname'), strip=True)
        props['group'] = ware.get('transport')
        props['volume'] = int(ware.get('volume'))
        props['tags'] = ware.get('tags', '').split(' ')
        props['illegal'] = ware.get('illegal', '').split(' ')

        price = get_xpath_attribs(ware, './price', {})
        props['price_min'] = int(price['min'])
        props['price_avg'] = int(price['average'])
        props['price_max'] = int(price['max'])

        productions = []
        for production in ware.xpath('./production'):
            pprops = {}
            pprops['time'] = float(production.get('time'))
            pprops['amount'] = int(production.get('amount'))
            pprops['method'] = production.get('method')
            pprops['name'] = \
                lresolver.resolve_string(production.get('name'), strip=True)

            consumption = {}
            for c_ware in production.xpath('./primary/ware'):
                consumption[c_ware.get('ware')] = int(c_ware.get('amount'))

            pprops['consumption'] = consumption

            productions.append(pprops)

        props['production'] = productions

        props['licence'] = \
            get_xpath_attrib(ware, './restriction[@licence]', 'licence', '')

        owners = []
        for owner in ware.xpath('./owner[@faction]'):
            owners.append(owner.get('faction'))

        props['owners'] = owners

        wares[ware_id] = props

    return wares
