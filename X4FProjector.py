#!/usr/bin/env python3

# Disable 'Module name "X4FProjector" doesn't conform to snake_case naming
# style (invalid-name)'
# pylint: disable=invalid-name

"""Main function for the project. See the help message."""

import argparse
import logging
import os
import sys

import exporters
import file_loaders
import lang
import loaders
import macros


LOG = logging.getLogger(__name__)


# I got some of those names/abbreviations from Wikipedia.
# Please don't bash me if I got something wrong, I'm not a qualified
# translator.
LANG_TABLE = {
    't/0001-L007.xml': ['ru', 'rus', 'russian', 'russkij', 'russkiy',
                        'русский'],
    't/0001-L033.xml': ['fr', 'fra', 'fre', 'french', 'français'],
    't/0001-L034.xml': ['es', 'sp', 'spa', 'spanish', 'español'],
    't/0001-L039.xml': ['it', 'ita', 'italian', 'italiano'],
    't/0001-L044.xml': ['en', 'eng', 'english'],
    't/0001-L049.xml': ['ge', 'de', 'ger', 'deu', 'german', 'deutsch',
                        'deutsche'],
    't/0001-L055.xml': ['pt', 'por', 'portuguese', 'português'],
    't/0001-L081.xml': ['ja', 'jpn', 'japanese', '日本語', 'nihongo'],
    't/0001-L082.xml': ['ko', 'kor', 'korean', '한국어', '韓國語', 'hangugeo'],
    't/0001-L086.xml': ['zh', 'zh-cn', 'chi', 'chi-cn', 'zho', 'zho-cn',
                        'chinese', 'chinese-cn', '汉语', 'hànyǔ'],
    't/0001-L088.xml': ['zh-tw', 'chi-tw', 'zho-tw', 'chinese-tw', '漢語'],
}


HELP_MESSAGE = """./X4FProjector -g path/to/x4_foundations/ export all \
-d ./x4-projected -f csv

Supported formats:
    - csv - Tabular, omits some information.
    - json - Structured.
    - yaml - Structured.


Example:
    ./X4FProjector.py -g path/to/x4 resolve-string 'This ship is \
{20101,30302}' 'That ship is {20101,30303}'
Output:
    This ship is Nemesis Vanguard
    That ship is Nemesis Sentinel

Example using German language:
    ./X4FProjector.py -g path/to/x4 -l de resolve-string 'This ship is \
{20101,30302}' 'That ship is {20101,30303}'
Output:
    This ship is Nemesis Angreifer
    That ship is Nemesis Verteidiger
"""


def list_extension_paths(game_root):
    """Get extension names and paths from the game root."""
    exts_dir = os.path.join(game_root, "extensions")
    if not os.path.isdir(exts_dir):
        return []

    extensions = []

    for ext_dir in os.scandir(exts_dir):
        if ext_dir.is_dir():
            extensions.append((ext_dir.name, ext_dir.path))

    return extensions


def cmd_resolve_strings(lresolver, resolve_strings):
    """Handle resolve-string command."""
    for string in resolve_strings:
        print(lresolver.resolve_string(string))

    return 0


def cmd_export(floader, lresolver, macro_db, export_objects, export_dir,
               export_format):
    """Handle export command."""

    objects = set(obj.strip().lower() for obj in export_objects)

    if 'all' in objects:
        objects = set(['engines', 'shields', 'ships', 'wares', 'weapons',
                       'missilelaunchers'])
        LOG.info('Exportint stats for all game objects: %s',
                 ', '.join(sorted(objects)))
    else:
        LOG.info('Exporting stats for %s', ', '.join(sorted(objects)))

    wares = None

    export_format = export_format.strip().lower()
    file_extension = exporters.AutoFormatter.get_extension(export_format)

    def make_path(obj):
        return os.path.normpath(os.path.join(
            export_dir, '{}.{}'.format(obj, file_extension)
        ))

    wares = {}

    for ext_name in [None] + floader.get_extensions():
        for obj in objects:
            if obj == 'engines':
                loaders.engine_loader(floader, lresolver, macro_db, ext_name)
            elif obj == 'missilelaunchers':
                loaders.missilelauncher_loader(floader, lresolver, macro_db,
                                               ext_name)
            elif obj == 'shields':
                loaders.shield_loader(floader, lresolver, macro_db, ext_name)
            elif obj == 'ships':
                loaders.ship_loader(floader, lresolver, macro_db, ext_name)
            elif obj == 'wares':
                wares.update(loaders.ware_loader(floader, lresolver, ext_name))
            elif obj == 'weapons':
                loaders.weapon_loader(floader, lresolver, macro_db, ext_name)
            else:
                raise ValueError('Unknown object type: {}'.format(obj))

        macro_db.resolve_dependencies()

    for obj in objects:
        dest = make_path(obj)

        if obj == 'engines':
            exporters.export_engines(macro_db, dest, export_format)
        elif obj == 'missilelaunchers':
            exporters.export_missilelaunchers(macro_db, dest, export_format)
        elif obj == 'shields':
            exporters.export_shields(macro_db, dest, export_format)
        elif obj == 'ships':
            exporters.export_ships(macro_db, dest, export_format)
        elif obj == 'wares':
            exporters.export_wares(wares, dest, export_format)
        elif obj == 'weapons':
            exporters.export_weapons(macro_db, dest, export_format)

    return 0


# pylint: disable=too-many-arguments
def main(command, verbose=False, game_root='./', file_loader='cat',
         language='en', resolve_strings=None, export_objects=None,
         export_dir='./', export_format='csv'):
    """Main function. Arguments are passed from the cmdline parser."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    floader = None
    file_loader = file_loader.strip().lower()
    if file_loader == 'cat':
        floader = file_loaders.CatFileLoader(game_root)
        floader.load_from_game_root()

        for ext_name, ext_dir in list_extension_paths(game_root):
            floader.load_extension(ext_name, ext_dir)
    elif file_loader == 'fs':
        floader = file_loaders.FSFileLoader(game_root)
    else:
        raise ValueError('Invalid file loader: {}'.format(file_loader))

    language = language.strip().lower()
    lresolver = lang.LanguageResolver()
    for (lang_file_path, lang_aliases) in LANG_TABLE.items():
        if language in lang_aliases:
            with floader.open_file(lang_file_path) as lang_file:
                lresolver.load_lang_file(language, lang_file)
            break

    if not lresolver.get_loaded_languages():
        raise ValueError('Unknown language: {}'.format(language))

    macro_db = macros.MacroDB(floader)

    if command == 'resolve-string':
        return cmd_resolve_strings(lresolver, resolve_strings)

    if command == 'export':
        return cmd_export(floader, lresolver, macro_db, export_objects,
                          export_dir, export_format)

    if not command:
        print('No command given. Exiting.')
        return 0

    raise ValueError('Invalid command: {}'.format(command))


def parse_arguments():
    """Build the cmdline parser and parse the arguments.
    Returns an argparse Namespace instance.
    """

    base_parser = argparse.ArgumentParser(add_help=False)

    base_parser.add_argument(
        '-v', '--verbose', action='store_true', default=argparse.SUPPRESS,
        help='Verbose output. Default: off.'
    )
    base_parser.add_argument(
        '-g', '--game-root', default=argparse.SUPPRESS,
        help='Path to the game installation. Default: current directory.'
    )
    base_parser.add_argument(
        '--file-loader', default=argparse.SUPPRESS, choices=['fs', 'cat'],
        help='File loader to use. Default: cat.'
    )
    base_parser.add_argument(
        '-l', '--lang', default=argparse.SUPPRESS, dest='language',
        help='Language used for names. Default: english.'
    )

    parser = argparse.ArgumentParser(
        prog='X4FProjector',
        parents=[base_parser],
        usage=HELP_MESSAGE
    )

    subparsers = parser.add_subparsers(dest='command')

    string_resolve_parser = subparsers.add_parser(
        'resolve-string', help='Resolve a language-dependent string.',
        parents=[base_parser]
    )

    string_resolve_parser.add_argument(
        metavar='strings', nargs='*', dest='resolve_strings'
    )

    export_parser = subparsers.add_parser(
        'export', help='Expot data about about game objects.',
        parents=[base_parser]
    )

    export_parser.add_argument(
        metavar='objects', nargs='*', default=['all'], dest='export_objects',
        help='What kind of objects to export. One or more of: all, engines, '
        'missilelaunchers, shields, ships, wares, weapons. Default: all.'
    )

    export_parser.add_argument(
        '-d', '--dir', default='.', dest='export_dir',
        help='Directory to export game data to. Default: current directory.'
    )

    export_parser.add_argument(
        '-f', '--format', default='csv', dest='export_format',
        help='Format to export as. Default: CSV.'
    )

    return parser.parse_args()


if __name__ == '__main__':
    ARGS = parse_arguments()
    sys.exit(main(**vars(ARGS)))
