"""Loads data about ships and equipment."""

import logging
import re
from misc import get_xpath_attrib, get_xpath_attribs, find_nodes_with_tag
from misc import get_path_in_ext


LOG = logging.getLogger(__name__)


# pylint: disable=too-many-statements,too-many-locals
def macro_parser(macro_id, macro_type, prop_node, lresolver):
    """Macro parser.

    Arguments:
    macro_id: macro id.
    macro_type: macro type, a.k.a. class.
    prop_node: macro's XML proprties node.
    lresolver: LanguageResolver used to resolve names.
    """
    props = {}

    if macro_type.startswith('ship_'):
        props['name'] = lresolver.resolve_string(
            get_xpath_attrib(prop_node, './identification', 'name'),
            strip=True
        )

        props['class'] = macro_type.replace('ship_', '')

        props['missile_storage'] = int(
            get_xpath_attrib(prop_node, './storage[@missile]', 'missile', 0)
        )
        props['hull'] = int(get_xpath_attrib(prop_node, './hull', 'max'))
        props['purpose'] = get_xpath_attrib(prop_node, './purpose', 'primary')
        props['type'] = get_xpath_attrib(prop_node, './ship', 'type')
        props['people'] = int(
            get_xpath_attrib(prop_node, './people', 'capacity', 0)
        )
        props['mass'] = float(get_xpath_attrib(prop_node, './physics', 'mass'))
        props['gas_gatherrate'] = int(
            get_xpath_attrib(prop_node, './gatherrate', 'gas', 0)
        )

        inertia = get_xpath_attribs(prop_node, './physics/inertia', {})
        props['inertia_pitch'] = float(inertia.get('pitch', 0))
        props['inertia_yaw'] = float(inertia.get('yaw', 0))
        props['inertia_roll'] = float(inertia.get('roll', 0))

        drag = get_xpath_attribs(prop_node, './physics/drag', {})
        props['drag_forward'] = float(drag.get('forward', 0))
        props['drag_reverse'] = float(drag.get('reverse', 0))
        props['drag_horizontal'] = float(drag.get('horizontal', 0))
        props['drag_vertical'] = float(drag.get('vertical', 0))
        props['drag_pitch'] = float(drag.get('pitch', 0))
        props['drag_yaw'] = float(drag.get('yaw', 0))
        props['drag_roll'] = float(drag.get('roll', 0))
    elif macro_type == 'cockpit':
        # nothing of interest here
        pass
    elif macro_type == 'spacesuit':
        props['name'] = lresolver.resolve_string(
            get_xpath_attrib(prop_node, './identification', 'name'),
            strip=True
        )

        props['hull'] = int(get_xpath_attrib(prop_node, './hull', 'max'))
        props['mass'] = float(get_xpath_attrib(prop_node, './physics', 'mass'))

        oxygen = get_xpath_attribs(prop_node, './oxygen', {})
        props['oxygen_maxtime'] = int(oxygen.get('maxtime'))
        props['oxygen_warningtime'] = int(oxygen.get('warningtime'))
    elif macro_type == 'storage':
        cargo = get_xpath_attribs(prop_node, './cargo', {})
        props['cargobay'] = int(cargo.get('max'))
        props['storage_type'] = cargo.get('tags')
    elif macro_type == 'engine':
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['makerrace'] = identification.get('makerrace')
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )

        boost = get_xpath_attribs(prop_node, './boost', {})
        props['boost_duration'] = float(boost.get('duration', 0))
        props['boost_thrust'] = float(boost.get('thrust', 0))
        props['boost_release'] = float(boost.get('release', 0))
        props['boost_attack'] = float(boost.get('attack', 0))

        travel = get_xpath_attribs(prop_node, './travel', {})
        props['travel_charge'] = float(travel.get('charge', 0))
        props['travel_attack'] = float(travel.get('attack', 0))
        props['travel_thrust'] = float(travel.get('thrust', 0))
        props['travel_release'] = float(travel.get('release', 0))

        thrust = get_xpath_attribs(prop_node, './thrust', {})
        props['thrust_forward'] = float(thrust.get('forward', 0))
        props['thrust_reverse'] = float(thrust.get('reverse', 0))
        props['thrust_strafe'] = float(thrust.get('strafe', 0))
        props['thrust_pitch'] = float(thrust.get('pitch', 0))
        props['thrust_yaw'] = float(thrust.get('yaw', 0))
        props['thrust_roll'] = float(thrust.get('roll', 0))

        angular = get_xpath_attribs(prop_node, './angular', {})
        props['angular_pitch'] = float(angular.get('pitch', 0))
        props['angular_roll'] = float(angular.get('roll', 0))

        hull = get_xpath_attribs(prop_node, './hull', {})
        props['hull'] = int(hull.get('max', -1))
        props['hull_integrated'] = int(hull.get('integrated', 0))
        props['hull_threshold'] = float(hull.get('threshold', 0))
    elif macro_type == 'dockingbay':
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )

        props['docksize'] = get_xpath_attrib(prop_node, './docksize', 'tags')

        dock = get_xpath_attribs(prop_node, './dock', {})
        props['dock_external'] = int(dock['external'])
        props['dock_capacity'] = int(dock.get('capacity', 1))
        props['dock_allow'] = int(dock.get('allow', 1))
        props['dock_storage'] = int(dock.get('storage', 0))
    elif macro_type == 'dockarea':
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )
    elif macro_type == 'shieldgenerator':
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['makerrace'] = identification.get('makerrace')
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )

        recharge = get_xpath_attribs(prop_node, './recharge', {})
        props['capacity'] = int(recharge['max'])
        props['recharge_rate'] = float(recharge['rate'])
        props['recharge_delay'] = float(recharge['delay'])

        hull = get_xpath_attribs(prop_node, './hull', {})
        props['hull'] = int(hull.get('max', -1))
        props['hull_integrated'] = int(hull.get('integrated', 0))
        props['hull_threshold'] = float(hull.get('threshold', 0))
    elif macro_type in ('weapon', 'turret', 'bomblauncher'):
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['makerrace'] = identification.get('makerrace')
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )

        props['bullet_class'] = \
            get_xpath_attrib(prop_node, './bullet', 'class')

        heat = get_xpath_attribs(prop_node, './heat', {})
        props['heat_overhead'] = int(heat.get('overheat', 0))
        props['heat_cooldelay'] = float(heat.get('cooldelay', 0))
        props['heat_coolrate'] = int(heat.get('coolrate', 0))
        props['heat_reenable'] = int(heat.get('reenable', 0))

        props['rotation_speed'] = float(
            get_xpath_attrib(prop_node, './rotationspeed', 'max', 0.0)
        )

        props['rotation_accel'] = float(
            get_xpath_attrib(prop_node, './rotationacceleration', 'max', 0.0)
        )

        reload_attrs = get_xpath_attribs(prop_node, './reload', {})
        props['reload_rate'] = float(reload_attrs.get('rate', 0))
        props['reload_time'] = float(reload_attrs.get('time', 0))

        zoom = get_xpath_attribs(prop_node, './zoom', {})
        props['zoom_factor'] = float(zoom.get('factor', 0))
        props['zoom_time'] = float(zoom.get('time', 0))
        props['zoom_delay'] = float(zoom.get('delay', 0))

        hull = get_xpath_attribs(prop_node, './hull', {})
        props['hull'] = int(hull.get('max', -1))
        props['hull_integrated'] = int(hull.get('integrated', 0))
        props['hull_threshold'] = float(hull.get('threshold', 0))
        props['hull_hittable'] = int(hull.get('hittable', 1))
    elif macro_type == 'bullet':
        bullet = get_xpath_attribs(prop_node, './bullet', {})
        props['speed'] = int(bullet.get('speed', 0))
        props['lifetime'] = float(bullet.get('lifetime', 0))
        props['range'] = int(bullet.get('range', 0))
        props['amount'] = int(bullet.get('amount', 0))
        props['barrelamount'] = int(bullet.get('barrelamount', 0))
        props['timediff'] = float(bullet.get('timediff', 0))
        props['angle'] = float(bullet.get('angle', 0))
        props['maxhits'] = int(bullet.get('maxhists', 0))
        props['ricochet'] = float(bullet.get('ricochet', 0))
        props['restitution'] = float(bullet.get('restitution', 0))
        props['scale'] = int(bullet.get('scale', 0))
        props['attach'] = int(bullet.get('attach', 0))
        props['chargetime'] = float(bullet.get('chargetime', 0))

        heat = get_xpath_attribs(prop_node, './heat', {})
        props['heat'] = int(heat.get('value', 0))
        props['heat_initial'] = int(heat.get('initia;', 0))

        reload_attrs = get_xpath_attribs(prop_node, './reload', {})
        props['reload_rate'] = float(reload_attrs.get('rate', 0))
        props['reload_time'] = float(reload_attrs.get('time', 0))

        damage = get_xpath_attribs(prop_node, './damage', {})
        dmg_val = damage.get('value', 0)
        props['dmg_hull'] = int(damage.get('hull') or dmg_val)
        props['dmg_shields'] = int(damage.get('shield') or dmg_val)
        props['dmg_min'] = int(damage.get('min', -1))
        props['dmg_max'] = int(damage.get('max', -1))
        props['dmg_repair'] = int(damage.get('repair', 0))
        props['dmg_delay'] = int(damage.get('delay', 0))

        mining_mult_xpath = './damage/multiplier[@mining]'
        props['dmg_mining_mult'] = int(
            get_xpath_attrib(prop_node, mining_mult_xpath, 'mining', 1)
        )
    elif macro_type in ('missilelauncher', 'missileturret'):
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['makerrace'] = identification.get('makerrace')
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )

        props['bullet_class'] = \
            get_xpath_attrib(prop_node, './bullet', 'class')

        props['rotation_speed'] = float(
            get_xpath_attrib(prop_node, './rotationspeed', 'max', 0.0)
        )

        props['capacity'] = int(
            get_xpath_attrib(prop_node, './storage', 'capacity', 0)
        )

        props['ammunition'] = \
            get_xpath_attrib(prop_node, './ammunition', 'tags')

        hull = get_xpath_attribs(prop_node, './hull', {})
        props['hull'] = int(hull.get('max', -1))
        props['hull_integrated'] = int(hull.get('integrated', 0))
        props['hull_threshold'] = float(hull.get('threshold', 0))
        props['hull_hittable'] = int(hull.get('hittable', 1))
    elif macro_type in ('bomb', 'missile'):
        identification = get_xpath_attribs(prop_node, './identification', {})
        props['name'] = lresolver.resolve_string(
            identification.get('name'),
            strip=True
        )
        props['makerrace'] = identification.get('makerrace')
        props['description'] = lresolver.resolve_string(
            identification.get('description'),
            strip=True
        )

        missile = get_xpath_attribs(prop_node, './missile', {})
        props['amount'] = int(missile.get('amount', 1))
        props['barrelamount'] = int(missile.get('barrelamount', 1))
        props['lifetime'] = float(missile.get('lifetime', 0))
        props['range'] = int(missile.get('range', 0))
        props['retarget'] = int(missile.get('retarget', 0))
        props['guided'] = int(missile.get('guided', 0))
        props['distribute'] = int(missile.get('distribute', 0))

        expl_dmg = get_xpath_attribs(prop_node, './explosiondamage', {})
        props['damage_hull'] = int(
            expl_dmg.get('hull') or expl_dmg.get('value') or 0
        )
        props['damage_shield'] = int(
            expl_dmg.get('shield') or expl_dmg.get('value') or 0
        )

        props['reload_time'] = float(
            get_xpath_attrib(prop_node, './reload', 'time', 0)
        )

        props['hull'] = int(
            get_xpath_attrib(prop_node, './hull', 'max')
        )

        props['contermeasure_resilience'] = float(
            get_xpath_attrib(prop_node, './countermeasure', 'resilience', -1)
        )

        lock = get_xpath_attribs(prop_node, './lock', {})
        props['lock_time'] = int(lock.get('time', 0))
        props['lock_range'] = int(lock.get('range', -1))
        props['lock_angle'] = float(lock.get('angle', -1))

        props['mass'] = float(get_xpath_attrib(prop_node, './physics', 'mass'))

        inertia = get_xpath_attribs(prop_node, './physics/inertia', {})
        props['inertia_pitch'] = float(inertia.get('pitch', 0))
        props['inertia_yaw'] = float(inertia.get('yaw', 0))
        props['inertia_roll'] = float(inertia.get('roll', 0))

        drag = get_xpath_attribs(prop_node, './physics/drag', {})
        props['drag_forward'] = float(drag.get('forward', 0))
        props['drag_reverse'] = float(drag.get('reverse', 0))
        props['drag_horizontal'] = float(drag.get('horizontal', 0))
        props['drag_vertical'] = float(drag.get('vertical', 0))
        props['drag_pitch'] = float(drag.get('pitch', 0))
        props['drag_yaw'] = float(drag.get('yaw', 0))
        props['drag_roll'] = float(drag.get('roll', 0))
    elif macro_type == 'buildmodule':
        pass
    elif macro_type == 'buildprocessor':
        pass
    elif macro_type == 'destructible':
        pass
    else:
        LOG.error('Failed to load macro properties: unhandled type %s for %s',
                  macro_type, macro_id)

    return props


def get_size_from_tags(tags):
    """Searches a tags string for a size tag and returns the size tag.
    Size tags: spacesuit, extrasmall, small, medium, large, extralarge.
    """
    match = re.search(
        r'\b(spacesuit|extrasmall|small|medium|large|extralarge)\b', tags
    )
    if match:
        return match[0]

    return ''


def get_component_size(comp_node, comp_name, conns_xpath, tag):
    """Gets the size of a component by looking for a connection node with a
    certain tag.

    Arguments:
    comp_node: component node.
    comp_name: name of the component. Used for logging.
    conns_xpath: XPath that references the connection nodes inside the
                 component node.
    tag: tag to look for.
    """
    size = ''

    for node in find_nodes_with_tag(comp_node, conns_xpath, tag):
        temp = get_size_from_tags(node.get('tags', ''))
        if temp and not size:
            size = temp
        elif temp and size:
            LOG.warning('Error when determine %s size for %s: too many'
                        '%s nodes found', tag, comp_name, tag)
            return size

    if not size:
        LOG.warning('Cannot determine %s size for %s: no %s nodes found',
                    tag, comp_name, tag)

    return size


# pylint: disable=too-many-branches
def component_parser(comp_name, comp_type, comp_node):
    """Component parser.

    Arguments:
    comp_name: name of the component.
    comp_type: type of the component.
    comp_node: component XML node.
    """
    props = {}
    conns_xpath = './connections/connection[@tags]'

    if comp_type.startswith('ship_'):
        def glen(gen):
            i = 0
            for _ in gen:
                i += 1

            return i

        props['num_engines'] = glen(
            find_nodes_with_tag(comp_node, conns_xpath, 'engine')
        )
        props['num_shields'] = glen(
            find_nodes_with_tag(comp_node, conns_xpath, 'shield')
        )
        props['num_weapons'] = glen(
            find_nodes_with_tag(comp_node, conns_xpath, 'weapon')
        )
        props['num_turrets'] = glen(
            find_nodes_with_tag(comp_node, conns_xpath, 'turret')
        )
        props['num_countermeasures'] = glen(
            find_nodes_with_tag(comp_node, conns_xpath, 'countermeasures')
        )
    elif comp_type == 'storage':
        pass
    elif comp_type == 'shieldgenerator':
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'shield')
    elif comp_type == 'engine' and comp_name.startswith('engine_'):
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'engine')
    elif comp_type == 'engine' and comp_name.startswith('generic_'):
        # no size in generic_engine components
        pass
    elif comp_type == 'engine' and comp_name.startswith('thruster_'):
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'thruster')
    elif comp_type == 'cockpit':
        pass
    elif comp_type == 'dockingbay':
        pass
    elif comp_type == 'dockarea':
        pass
    elif comp_type in ('weapon', 'bomblauncher'):
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'weapon')
    elif comp_type == 'turret':
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'turret')
    elif comp_type == 'bullet':
        pass
    elif comp_type == 'missilelauncher':
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'missile')
    elif comp_type == 'missileturret':
        props['size'] = \
            get_component_size(comp_node, comp_name, conns_xpath, 'missile')
    elif comp_type in ('missile', 'bomb'):
        pass
    elif comp_type == 'bomblauncher':
        props['size'] = get_component_size(comp_node, comp_name, conns_xpath,
                                           'bomblauncher')
    elif comp_type == 'buildmodule':
        pass
    elif comp_type == 'buildprocessor':
        pass
    elif comp_type == 'destructible':
        pass
    else:
        LOG.error('Failed to load component properties: unhandled type %s '
                  'for %s', comp_type, comp_name)

    return props


def ship_loader(floader, lresolver, macro_db, ext_name):
    """Loads ship game macro files and returns ship data.
    This function will set the macro_db's macro parser and component parser.

    Arguments:
    floader: FileLoader to use.
    lresolver: LanguageResolver used to resolve ship names.
    macro_db: MacroDB used to load macros.
    ext_name: extension to load ships from. Use None for the base game.
    """

    # pylint: disable=no-value-for-parameter
    macro_db.set_macro_parser(
        lambda *args: macro_parser(*args, lresolver=lresolver)
    )
    macro_db.set_component_parser(component_parser)

    units_root_xml = get_path_in_ext('assets/units', ext_name)

    for ship_size in ['xs', 's', 'm', 'l', 'xl']:
        ships_path = '{}/size_{}/macros/'.format(units_root_xml, ship_size)
        for entry in floader.list_files(ships_path):
            macro_db.load_macro_xml_file(entry.path)


def shield_loader(floader, lresolver, macro_db, ext_name):
    """Loads shield game macro files and returns shield data.
    This function will set the macro_db's macro parser and component parser.

    Arguments:
    floader: FileLoader to use.
    lresolver: LanguageResolver used to resolve ship names.
    macro_db: MacroDB used to load macros.
    ext_name: extension to load shields from. Use None for the base game.
    """
    # pylint: disable=no-value-for-parameter
    macro_db.set_macro_parser(
        lambda *args: macro_parser(*args, lresolver=lresolver)
    )
    macro_db.set_component_parser(component_parser)

    shields_xml_root = get_path_in_ext(
        'assets/props/SurfaceElements/macros/', ext_name)

    for entry in floader.list_files(shields_xml_root):
        if not entry.name.startswith('shield_'):
            continue

        macro_db.load_macro_xml_file(entry.path)


def engine_loader(floader, lresolver, macro_db, ext_name):
    """Loads engine game macro files and returns engine data.
    This function will set the macro_db's macro parser and component parser.

    Arguments:
    floader: FileLoader to use.
    lresolver: LanguageResolver used to resolve ship names.
    macro_db: MacroDB used to load macros.
    ext_name: extension to load engines from. Use None for the base game.
    """
    # pylint: disable=no-value-for-parameter
    macro_db.set_macro_parser(
        lambda *args: macro_parser(*args, lresolver=lresolver)
    )
    macro_db.set_component_parser(component_parser)

    egines_xml_root = get_path_in_ext('assets/props/Engines/macros/', ext_name)

    for entry in floader.list_files(egines_xml_root):
        if not entry.name.startswith('engine_') and \
           not entry.name.startswith('thruster_'):
            continue

        macro_db.load_macro_xml_file(entry.path)


def weapon_loader(floader, lresolver, macro_db, ext_name):
    """Loads weapon game macro files and returns weapon data.
    This function will set the macro_db's macro parser and component parser.

    Arguments:
    floader: FileLoader to use.
    lresolver: LanguageResolver used to resolve ship names.
    macro_db: MacroDB used to load macros.
    ext_name: extension to load weapons from. Use None for the base game.
    """
    # pylint: disable=no-value-for-parameter
    macro_db.set_macro_parser(
        lambda *args: macro_parser(*args, lresolver=lresolver)
    )
    macro_db.set_component_parser(component_parser)

    weapon_xml_root = get_path_in_ext('assets/props/WeaponSystems', ext_name)

    for weapon_type in ['capital', 'heavy', 'mining', 'standard', 'spacesuit',
                        'energy', 'xref_parts']:
        path = '{}/{}/macros/'.format(weapon_xml_root, weapon_type)

        try:
            entries = list(floader.list_files(path))
        except ValueError:
            continue

        for entry in entries:
            if not entry.name.startswith('weapon_') and \
               not entry.name.startswith('turret_') and \
               not entry.name.startswith('spacesuit_gen_laser_') and \
               not entry.name.startswith('spacesuit_gen_repairweapon_'):
                continue

            macro_db.load_macro_xml_file(entry.path)

    bullet_xml_root = get_path_in_ext('assets/fx/weaponFx/macros', ext_name)

    for entry in floader.list_files(bullet_xml_root):
        if not entry.name.startswith('bullet_'):
            continue

        macro_db.load_macro_xml_file(entry.path)


def missilelauncher_loader(floader, lresolver, macro_db, ext_name):
    """Loads missile launcher game macro files and returns missile launchers
    data. This function will set the macro_db's macro parser and component
    parser.

    Arguments:
    floader: FileLoader to use.
    lresolver: LanguageResolver used to resolve ship names.
    macro_db: MacroDB used to load macros.
    ext_name: extension to load missile launchers from.
              Use None for the base game.
    """
    # pylint: disable=no-value-for-parameter
    macro_db.set_macro_parser(
        lambda *args: macro_parser(*args, lresolver=lresolver)
    )
    macro_db.set_component_parser(component_parser)

    weapon_xml_root = get_path_in_ext('assets/props/WeaponSystems', ext_name)

    for missile_type in ['dumbfire', 'guided', 'torpedo', 'spacesuit']:
        path = '{}/{}/macros/'.format(weapon_xml_root, missile_type)

        try:
            entries = list(floader.list_files(path))
        except ValueError:
            continue

        for entry in entries:
            if not entry.name.startswith('weapon_') and \
               not entry.name.startswith('turret_') and \
               not entry.name.startswith('spacesuit_gen_bomblauncher_'):
                continue

            macro_db.load_macro_xml_file(entry.path)

    missiles_xml_root = get_path_in_ext(
        'assets/props/WeaponSystems/missile/macros', ext_name)

    for entry in floader.list_files(missiles_xml_root):
        if not entry.name.startswith('missile_'):
            continue

        macro_db.load_macro_xml_file(entry.path)

    bomb_xml_root = get_path_in_ext('assets/fx/weaponFx/macros', ext_name)

    for entry in floader.list_files(bomb_xml_root):
        if not entry.name.startswith('bomb_'):
            continue

        macro_db.load_macro_xml_file(entry.path)
