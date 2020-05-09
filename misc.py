"""Misc functions that provide commonly-used functionalities."""

import re
import logging


LOG = logging.getLogger(__name__)


def get_xpath_attrib(node, xpath, attrib, default=None):
    """Returns the value of an attribute of the first node selected by an XPath
    query.
    If multiple nodes that match the XPath are found then a warning will be
    printed.

    Arguments:
    node: node to perform the XPath query on.
    xpath: XPath query.
    attrib: attribute to look up.
    default: value to return if no node is found or the attribute is missing.
    """
    nodes = node.xpath(xpath)
    if isinstance(nodes, list):
        if nodes:
            if len(nodes) > 1:
                LOG.warning('More than one node matched xpath %s', xpath)
            return nodes[0].get(attrib, default)

        return default

    return nodes.get(attrib, default)


def get_xpath_attribs(node, xpath, default=None):
    """Returns the attributes dict of the first node selected by an XPath
    query.
    If multiple nodes that match the XPath are found then a warning will be
    printed.

    Arguments:
    node: node to perform the XPath query on.
    xpath: XPath query.
    default: value to return if no node is found or the attribute is missing.
    """
    nodes = node.xpath(xpath)
    if isinstance(nodes, list):
        if nodes:
            if len(nodes) > 1:
                LOG.warning('More than one node matched xpath %s', xpath)
            return nodes[0].attrib

        return default

    return nodes.attrib


def find_nodes_with_tag(root_node, xpath, tag):
    """Performs an XPath query on a node and yields nodes that have a 'tags'
    attribute that contains the given tag.

    Arguments:
    root_node: node to perform the XPath query on.
    xpath: XPath query.
    tag: requested tag.
    """

    # regex that matches the tag in a tags string
    tag_re = re.compile(r'\b{}\b'.format(tag))

    for node in root_node.xpath(xpath):
        if tag_re.search(node.get('tags', '')):
            yield node

def get_path_in_ext(path, ext_name):
    """Transform a game path relative to an extension root into a game path
    relative to the game root.

    Arguments:
    path: game path relative to the extension path
    ext_name: extension name
    """
    if ext_name:
        return "/extensions/{}/{}".format(ext_name, path)

    return path