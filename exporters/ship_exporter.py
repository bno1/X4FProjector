"""Exporter for ships."""

import copy
import logging
from exporters.helpers import FileLikeProvider, AutoFormatter


LOG = logging.getLogger(__name__)


def tabular_generator(ships):
    """Generator that produces rows for tabular formats (CSV) from the dict
    produced by export_ships. The generated rows don't include all the data
    about the ships.
    """

    cols = [
        'name',
        'class',
        'type',
        'purpose',
        'hull',
        'people',
        'cargobay',
        'storage',
        'missile_storage',
        'drone_storage',
        'num_engines',
        'num_shields',
        'num_weapons',
        'num_turrets',
        'num_countermeasures',
        's_docks',
        'm_docks',
        'shipstorage_s',
        'shipstorage_m',
        'launchtubes_s',
        'launchtubes_m',
        'mass',
        'drag_forward',
        'drag_reverse',
        'drag_horizontal',
        'drag_vertical',
        'drag_pitch',
        'drag_yaw',
        'drag_roll',
        'inertia_pitch',
        'inertia_yaw',
        'inertia_roll',
    ]

    # output header
    yield ['id'] + cols

    # output data
    for ship_id in sorted(ships.keys()):
        ship = copy.copy(ships[ship_id])

        ship['storage'] = ' '.join(ship['storage'])

        yield [ship_id] + [ship.get(col) for col in cols]


def process_connections(macro_db, connections, ship, ship_id):
    """Recursively traverses ship connections and loads data into the ship
    dictionary.

    Arguments:
    macro_db: MacroDB.
    connections: list of names of macros connected to the ship.
    ship: dictionary containing ship data.
    ship_id: game id of the ship. Used for logging.
    """
    for (_, macro_ref) in connections:
        macro = macro_db.macros.get(macro_ref)
        if not macro:
            continue

        if macro.type == 'cockpit':
            pass
        elif macro.type == 'dockarea':
            pass
        elif macro.type == 'buildmodule':
            pass
        elif macro.type == 'buildprocessor':
            pass
        elif macro.type == 'dockingbay':
            bay = copy.copy(macro.properties)
            bay['name'] = macro.name

            bays = ship['dockingbays']
            bays.append(bay)

            docksize = bay['docksize']

            if bay['dock_storage']:
                if 'dock_xs' in docksize:
                    ship['drone_storage'] += bay['dock_capacity']

                if 'dock_s' in docksize:
                    ship['shipstorage_s'] += bay['dock_capacity']

                if 'dock_m' in docksize:
                    ship['shipstorage_m'] += bay['dock_capacity']

            if macro_ref.startswith('dockingbay'):
                if 'dock_s' in docksize:
                    ship['s_docks'] += bay['dock_capacity']

                if 'dock_m' in docksize:
                    ship['m_docks'] += bay['dock_capacity']

            if macro_ref.startswith('launchtube'):
                if 'dock_s' in docksize:
                    ship['launchtubes_s'] += bay['dock_capacity']

                if 'dock_m' in docksize:
                    ship['launchtubes_m'] += bay['dock_capacity']

        elif macro.type == 'storage':
            ship['cargobay'] = macro.properties['cargobay']
            ship['storage'] = macro.properties['storage_type'].split(' ')
        else:
            LOG.warning('Unhandled connection type %s when exporting ship %s',
                        macro.type, ship_id)

        if macro.connections:
            process_connections(macro_db, macro.connections, ship, ship_id)


def export_ships(macro_db, destination=None, output_format='csv'):
    """Parses data about ships from the MacroDB and exports it.
    Dependencies in the MacroDB must be resolved, otherwise incomplete data
    will be exported.

    Arguments:
    macro_db: MacroDB into which ships were loaded.
    destination: output type and destination. Supported values:
                 - None: output to string and return it.
                 - string: interpreted as a file path. Writes the output to the
                           file and returns None.
                 - other: interpreted as file-like object. Writes the output to
                          it and returns None.
    output_format: format for outputting the data. See helper.AutoFormatter for
                   more details.
    """
    output = FileLikeProvider(destination)

    ships = {}

    for size in ['xs', 's', 'm', 'l', 'xl']:
        for ship_id in macro_db.macros_by_type['ship_' + size]:
            macro = macro_db.macros[ship_id]

            ship = copy.copy(macro.properties)

            # add attributes extracted from connections
            ship['dockingbays'] = []
            ship['cargobay'] = 0
            ship['storage'] = ''
            ship['s_docks'] = 0
            ship['m_docks'] = 0
            ship['drone_storage'] = 0
            ship['shipstorage_s'] = 0
            ship['shipstorage_m'] = 0
            ship['launchtubes_s'] = 0
            ship['launchtubes_m'] = 0

            process_connections(macro_db, macro.connections, ship, ship_id)
            ships[ship_id] = ship

    formatter = AutoFormatter(output_format)
    with output as output_file:
        if formatter.is_tabular():
            formatter.output(tabular_generator(ships), output_file)
        elif formatter.is_structured():
            formatter.output(ships, output_file)
        else:
            raise ValueError('Unknown formatter type for format {}'
                             .format(output_format))

    return output.get_return()
