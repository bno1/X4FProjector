"""Utilities for handling language-related things."""

import re
import logging
from lxml import etree


LOG = logging.getLogger(__name__)


class LanguageResolver:
    """Resolves language-aware strings.
    X4 uses a template system where a string can contain '{page_id, text_id}'
    fields which are substituted using language files found in 't/*.xml'.

    Note: The game seems to use country calling codes as codes for the language
          files. Possible features: automatic language name -> code translator.
    """

    def __init__(self):
        """Initializes the LanguageResolver."""
        self.lang_trees = {}
        self.default_lang = None

    def load_lang_file(self, lang_name, lang_file):
        """Loads a language file.
        If this is the first language loaded and no default language was
        configured yet then the default language will be set to this language.

        Arguments:
        lang_name: name that will be used to refer to this language.
        lang_file: file path, bytes or file-like object containing the game XML
                   file defining the language strings.
        """
        self.lang_trees[lang_name] = etree.parse(lang_file)

        if self.default_lang is None:
            self.default_lang = lang_name

    def set_default_lang(self, lang_name):
        """Sets the default language."""
        self.default_lang = lang_name

    def get_loaded_languages(self):
        """Returns the list of languages loaded."""
        return list(self.lang_trees.keys())

    def resolve_string(self, template, lang_name=None, strip=False):
        """Resolve a template string using the given language.
        Returns the resolved string.

        Arguments:
        template: the template string.
        lang_name: name of the loaded language to use. Raises KeyError if no
                   loaded language has this name.
        strip: strip heading and trailing white spaces from the result.
        """
        if not template:
            return template

        if lang_name is None:
            lang_name = self.default_lang

        if lang_name not in self.lang_trees:
            raise KeyError('Language {} not loaded'.format(lang_name))

        lang_tree = self.lang_trees[lang_name]

        def resolve_field(match):
            # look up the page and text id in the lang file
            page_id = match[1]
            t_id = match[2]

            ts_xpath = "./page[@id='{}']/t[@id='{}']".format(page_id, t_id)
            text_nodes = lang_tree.xpath(ts_xpath)
            if not text_nodes:
                LOG.error('Failure while resolving string: cannot resolve '
                          'filed %s', match[0])

                # return the matched field
                return match[0]

            text = text_nodes[0].text

            # template strings sometimes contain comments in paranthesis.
            # remove all comments inside unescaped paranthesis pairs.
            return re.sub(r'(?<!\\)\(.*?(?<!\\)\)', '', text)

        text_old = None
        text_new = template

        # resolve the template until no more substitutions take place
        while text_new != text_old:
            text_old = text_new

            # resolve all fields
            text_new = re.sub(r'\{\s*(\d+)\s*,\s*(\d+)\s*\}',
                              resolve_field, text_new)

        # unescape characters
        text = re.sub(r'\\(.)', r'\1', text_new)
        if strip:
            text = text.strip()

        return text
