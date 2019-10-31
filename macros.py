"""Loading and processing of game macro and component files."""

import copy
import re
import logging
from lxml import etree


LOG = logging.getLogger(__name__)


class Macro:
    """Class that describes a macro.

    Members:
    name: in-game name of the macro.
    type: macro type, a.k.a. class. E.g. engine, shieldgenerator, ship_xl.
    connections: list of (connection_id, macro_id) of connected components.
    properties: a dictionary containing parsed macro data.
    """

    __slots__ = ('name', 'type', 'connections', 'properties')

    def __init__(self, name, macro_type, properties):
        self.name = name
        self.type = macro_type
        self.connections = []
        self.properties = properties

    def add_connection(self, conn_id, macro_id):
        """Add a connection to this macro.
        Used by MacroDB.
        """
        self.connections.append((conn_id, macro_id))


def noop_parser(_name, _entity_type, _node):
    """Macro and component parser that does nothing and returns an empty dict.
    Used as default parsers for Macro.
    """
    return {}


class MacroDB:
    """Database that takes care of loading macros and components and resolving
    dependencies.
    Macros and components are processed via custom functions passed through
    set_macro_parser and set_component_parser.

    Members:
    floader: the file loader used to resolve dependencies.
    macros: dict of Macro objects keyed by the macro id.
    macros_by_type: dict of macro_type -> [macro_name].
    dependencies: unresolved dependencies.
    macro_path_resolver: function that resolves a macro id to a game .xml file
                         path.
    component_path_resolver: function that resolve a component name to a game
                             .xml file path.
    macro_parser: function that receives the macro name, macro type (class) and
                  macro <properties> node and returns a dictionary that will be
                  saved as macro's properties.
    component_parser: function that receives the component name, component type
                      and component XML node and returns a dictionary that will
                      be combined into the one returned by macro_parser.
    """

    def __init__(self, floader):
        """Initialize the macro database.

        Arguments:
        floader: file loader that will be used by this object.
        """
        self.macro_index = {}
        self.component_index = {}
        self.floader = floader
        self.macros = {}
        self.macros_by_type = {}
        self.dependencies = set()

        self.macro_parser = noop_parser
        self.component_parser = noop_parser

        self._load_index('index/macros.xml', self.macro_index)
        self._load_index('index/components.xml', self.component_index)

        self._fix_missing_index_entries()

    def _load_index(self, path, dest):
        """Load an index file.

        Arguments:
        path: game path to the index file.
        dest: dictionary into which to insert index entries.
        """

        with self.floader.open_file(path) as idx_file:
            idx_tree = etree.parse(idx_file)

        for entry in idx_tree.xpath('./entry[@name][@value]'):
            dest[entry.get('name')] = entry.get('value').replace('\\', '/') + '.xml'

    def _fix_missing_index_entries(self):
        """Fix indexes. Add missing entries or repair broken ones."""

        self.component_index['cockpit_invisible_escapepod'] = \
            'assets/units/size_s/cockpit_invisible_escapepod.xml'

    def set_macro_parser(self, macro_parser):
        """Sets the macro parser."""
        self.macro_parser = macro_parser

    def set_component_parser(self, component_parser):
        """Sets the component parser."""
        self.component_parser = component_parser

    def load_component_properties(self, comp_name):
        """Loads a component, parses it and returns the properties dict.

        Arguments:
        comp_name: name (id) of component to load.
        """

        path = self.component_index.get(comp_name)

        if not path:
            LOG.error('Failed to load component %s, not found in index',
                      comp_name)
            return {}

        with self.floader.open_file(path) as comp_file:
            comp_tree = etree.parse(comp_file)

        comp_xpath = "./component[@name='{}']".format(comp_name)
        comp_nodes = comp_tree.xpath(comp_xpath)
        if len(comp_nodes) > 1:
            LOG.error('Failed to load component properties from %s: '
                      'too many <properties> nodes', path)
        elif comp_nodes:
            comp_node = comp_nodes[0]

            # some pesky component has a space in its class
            comp_type = comp_node.get('class').strip()
            return self.component_parser(comp_name, comp_type, comp_node)
        else:
            LOG.warning('No components with name %s in file %s',
                        comp_name, path)

        return {}

    def load_macro_xml_file(self, path):
        """Loads macros from a game .xml file.

        Arguments:
        path: path to game .xml file.
              E.g.: assets/props/Engine/macros/engine_(...)_macro.xml
        """

        with self.floader.open_file(path) as macro_file:
            tree = etree.parse(macro_file)
        found_macro = False

        for macro_node in tree.xpath('./macro[@name][@class]'):
            found_macro = True
            macro_name = macro_node.get('name')
            macro_type = macro_node.get('class')
            properties = {}

            prop_nodes = macro_node.xpath('./properties')
            if len(prop_nodes) > 1:
                LOG.error('Failed to load macro properties from %s: too '
                          'many <properties> nodes', path)
            elif prop_nodes:
                # parse properties
                properties = \
                    self.macro_parser(macro_name, macro_type, prop_nodes[0])

            comp_nodes = macro_node.xpath('./component')
            if len(comp_nodes) > 1:
                LOG.error('Failed to load component properties from %s: '
                          'too many <properties> nodes', path)
            elif comp_nodes:
                comp_name = comp_nodes[0].get('ref')

                # parse properties from the component
                comp_props = self.load_component_properties(comp_name)
                properties.update(comp_props)

            macro = Macro(macro_name, macro_type, properties)

            connections_xpath = './connections/connection[@ref]'
            for conn_node in macro_node.xpath(connections_xpath):
                conn_ref = conn_node.get('ref')

                for conn_m_node in conn_node.xpath('./macro[@ref]'):
                    macro_ref = conn_m_node.get('ref')
                    if macro_ref not in self.macros:
                        self.dependencies.add(macro_ref)

                    macro.add_connection(conn_ref, macro_ref)

            # save macro, remove dependency if it exists
            self.macros[macro_name] = macro
            self.dependencies.discard(macro_name)

            t_macros = self.macros_by_type.setdefault(macro_type, [])
            t_macros.append(macro_name)

        if not found_macro:
            LOG.warning('No macros found in file %s', path)

    def _resolve_step(self):
        """One step in the dependency resolution algorithm.
        Returns true if the set of dependencies has changed.
        """

        # step 1: remove deps that are satisfied just to be sure
        for ref in list(self.dependencies):
            if ref in self.macros:
                self.dependencies.remove(ref)

        # step 2: make a copy of the dependency set
        deps_before = copy.deepcopy(self.dependencies)

        # step 3: try to load dependencies
        for ref in deps_before:
            path = self.macro_index.get(ref)
            if not path:
                LOG.error('Failed to load ref %s, not found in index', ref)
                continue

            if not self.floader.file_exists(path):
                LOG.error('Failed to load ref %s, file %s not found', ref, path)
                continue

            self.load_macro_xml_file(path)

        # step 4: return True if the new dependency set is different
        return deps_before != self.dependencies

    def resolve_dependencies(self):
        """Loads macros that aren't loaded yet but that are referred to by
        loaded macros.
        Returns True if all dependencies were resolved.
        """

        # while there are dependencies resolve them
        # when the set of dependencies doesn't change anymore stop
        while self.dependencies:
            if not self._resolve_step():
                LOG.error('Failed to resolve all dependencies. Remaining: %s',
                          self.dependencies)
                break

        # return True if no dependencies left
        return not self.dependencies
