"""Loaders for game files."""

import io
import logging
import os
from collections import namedtuple


LOG = logging.getLogger(__name__)


# Entry returned by list_files methods
Entry = namedtuple('Entry', ['path', 'name'])


def split_game_path(path):
    """Split a game path into individual components."""

    # filter out empty parts that are caused by double slashes
    return [p for p in path.split('/') if p]


class FileLoader:
    """Base class for file loaders."""

    def open_file(self, path):
        """Open file.
        Returns a binary file-like object.

        Arguments:
        path: path from game data files.
              E.g.  'assets/units/size_xl/ship_par_xl_carrier_01.xml'
        """
        raise NotImplementedError()

    def file_exists(self, path):
        """Check if file exists.
        Returns True/False.

        Arguments:
        path: path to game data file. See open_file().
        """
        raise NotImplementedError()

    def list_files(self, path):
        """List game files under a game directory.
        Returns an iterable over Entry objects.

        Arguments:
        path: path to game data directory. See open_file().
        """
        raise NotImplementedError()


class FSFileLoader:
    """File System File Loader.
    Loads game files that have been extracted using X Rebirth Cat tool or
    another tool.
    When extracting the files you MUST keep the folder hierarchy.
    """

    def __init__(self, files_root='./'):
        """Initialize file loader.

        Arguments:
        files_root: location of the extracted game files.
        """
        self.root = os.path.normpath(files_root)

    def _resolve(self, path):
        """Resolves a game file path to a file system path."""
        return os.path.join(self.root, path)

    def open_file(self, path):
        """Open game file."""
        return open(self._resolve(path), 'rb')

    def file_exists(self, path):
        """Check if file exists."""
        return os.path.isfile(self._resolve(path))

    def list_files(self, path):
        """List game files under a game directory."""
        for entry in os.scandir(self._resolve(path)):
            if entry.is_file():
                yield Entry(entry.path, entry.name)


class DatGameFile(io.RawIOBase):
    """A wrapper over a file object that restricts operations to a limited
    zone of the file defined by offset and size.
    It is used to read game files inside .dat files.
    Doesn't support truncation and writing.

    Members:
    dat_file: underlying .dat file.
    start: position of the begining of the game file.
    end: position of the end of the game file.
    """

    def __init__(self, dat_file, offset, size):
        """Initialize a game file.

        Arguments:
        dat_file: underlying .dat file.
        offset: offset from the start of dat_file of the game file.
        size: size of the game file.
        """
        super(DatGameFile, self).__init__()

        self.dat_file = dat_file
        self.start = offset
        self.end = offset + size

        # seek to the game file
        self.dat_file.seek(self.start, io.SEEK_SET)

    def _clamp_op(self, size):
        """Used to clamp the size of operations performed on the .dat in order
        to not go outside the game file.
        """
        max_size = max(0, self.end - self.dat_file.tell())

        if size < 0:
            # operation is performed until EOF is reached. limit to max_size.
            return max_size

        # don't go outside max_size.
        return min(size, max_size)

    def _clamp_pos(self, offset):
        """Used to clamp a .dat file offset to remain inside the game file."""
        return min(max(offset, self.start), self.end)

    def close(self):
        """Close underlying file."""
        self.dat_file.close()

    @property
    def closed(self):
        """Check underlying file status."""
        return self.dat_file.closed

    def fileno(self):
        """Underyling file descriptor."""
        return self.dat_file.fileno()

    def flush(self):
        """Flush underlying file."""
        return self.dat_file.flush()

    def isatty(self):
        """Check if underlying file is interactive."""
        return self.dat_file.isatty()

    def readable(self):
        """Check if underlying file is readable."""
        return self.dat_file.readable()

    def read(self, size=-1):
        """Read from the game file.
        The operation is clamped to not escape the game file boundaries.
        """
        return self.dat_file.read(self._clamp_op(size))

    def readall(self):
        """Read the whole game file.
        The operation is clamped to not escape the game file boundaries.
        """
        size = self._clamp_op(-1)

        buf = self.read(size)
        while len(buf) < size:
            buf += self.read(size - len(buf))

        return buf

    def readinto(self, b):
        """Read the game file into a buffer.
        The operation is clamped to not escape the game file boundaries.
        """
        size = self._clamp_op(len(b))

        return self.dat_file.readinto(b[0:size])

    def readline(self, size=-1):
        """Read a line from the game file.
        The operation is clamped to not escape the game file boundaries.
        """
        return self.dat_file.readline(self._clamp_op(size))

    def readlines(self, hint=-1):
        """Read lines from the game file.
        The operation is clamped to not escape the game file boundaries.
        """
        return self.dat_file.readlines(self._clamp_op(hint))

    def seek(self, offset, whence=io.SEEK_SET):
        """Seek the game file.
        Returns the final absolute position in the game file.
        The operation is clamped to not escape the game file boundaries.
        """
        abs_pos = None

        if whence == io.SEEK_SET:
            abs_pos = self._clamp_pos(offset + self.start)
        elif whence == io.SEEK_CUR:
            abs_pos = self._clamp_pos(offset + self.dat_file.tell())
        elif whence == io.SEEK_END:
            abs_pos = self._clamp_pos(offset + self.end)
        else:
            raise ValueError('Invalid seek whence: {}'.format(whence))

        self.dat_file.seek(io.SEEK_SET, abs_pos)
        return abs_pos - self.start

    def seekable(self):
        """Check if the underlying file is seekable."""
        return self.dat_file.seekable()

    def tell(self):
        """Return the current position in the game file."""
        return self.dat_file.tell() - self.start

    def truncate(self):
        """Not implemented."""
        raise NotImplementedError('Truncation is not supported')

    def writable(self):
        """Returns false, writing is not supported."""
        # return self.dat_file.writable()
        return False

    def write(self, b):
        """Not implemented."""
        raise NotImplementedError('Writing is not supported')

    def writelines(self, lines):
        """Not implemented."""
        raise NotImplementedError('Writing is not supported')

    def __del__(self):
        return self.dat_file.__del__()


CatEntry = namedtuple(
    'CatEntry',
    ['dat_path', 'name', 'size', 'offset']
)


class DirNode:
    """Directory node used by the CatFileLoader to represent the game file
    structure.

    Members:
    files: dictionary or file name -> CatEntry.
    children: dictionary of directory name -> DirNode.
    """

    # optimization: http://book.pythontips.com/en/latest/__slots__magic.html
    __slots__ = ('files', 'children')

    def __init__(self):
        """Initialize node with empty files and empty children."""

        self.files = {}
        self.children = {}


class CatFileLoader:
    """File loader that directly reads game .cat and .dat files.
    Cat files should be loaded in the order of highest to lowest priority.

    Members:
    game_root: path to the game installation.
    file_tree: DirNode instance representing the root of the game files
               hierarchy.
    data_files: pairs of (cat_path, dat_path) of data files to load, ordered
                from lowest to highest priority. Those are consumed from
                the tail to the head by the _load_next_cat_file function.
    loaded: set of path to loaded .cat files. This is used to avoid loading
            game files twice in case self.load_from_game_root is called
            multiple times.
    """

    def __init__(self, game_root='./'):
        """Initializes the cat loader.

        Arguments:
        game_root: path to game installation, where the .cat and .dat files are
                   stored.
        """
        self.game_root = game_root
        self.file_tree = DirNode()
        self.data_files = []
        self.loaded = set()

    def _load_cat_file(self, cat_path, dat_path):
        """Loads a .cat file and stores entries in the file tree.
        The entries will reference the .dat file.
        Returns True if the .cat file is parsed and loaded sucessfully.
        This function will NOT override already existing entries.

        Arguments:
        cat_path: path to .cat file.
        dat_path: path to .dat file.
        """
        file_offset = 0
        entries = []

        LOG.info('Loading .cat file %s', cat_path)

        # first parse entries
        # if the cat file is malformed this block will return, so the file
        # won't be partially loaded
        with open(cat_path, 'r') as cat_file:
            for line_no, line in enumerate(cat_file):
                if not line:
                    continue

                # match 'path size timestamp hash' format
                # path might contain spaces, so a rsplit is needed
                parts = line.rsplit(' ', 3)
                if len(parts) != 4:
                    LOG.error('Cat file %s has invalid entry on line %s',
                              cat_path, line_no + 1)
                    return False

                game_path = split_game_path(parts[0])
                size = int(parts[1])
                offset = file_offset
                file_offset += size

                if not game_path:
                    LOG.error('Cat file %s contains malformed game file path '
                              '%s on line %s', cat_path, parts[0], line_no + 1)
                    continue

                file_name = game_path[-1]
                game_path = game_path[:-1]

                entries.append((
                    game_path,
                    CatEntry(dat_path, file_name, size, offset)
                ))

        file_tree = self.file_tree

        # now add entries to the file tree
        for (game_path, entry) in entries:
            k = file_tree

            for directory in game_path:
                if directory not in k.children:
                    k.children[directory] = DirNode()

                k = k.children[directory]

            if entry.name not in k.files:
                k.files[entry.name] = entry

        self.loaded.add(cat_path)

        return True

    def _load_next_cat_file(self):
        """Loads the next cat file in order from highest to lowest priority.
        Works by removing the last pair of self.data_files (if any) and loading
        it.
        Returns False if no new data file can be loaded.
        """
        loaded = False

        while self.data_files and not loaded:
            (cat_path, dat_path) = self.data_files.pop()

            if cat_path not in self.loaded:
                loaded = self._load_cat_file(cat_path, dat_path)

        return loaded

    def load_from_game_root(self):
        """Looks .cat and .dat files in the game's root directory and records
        them in self.data_files. Those files will be loaded lazily when needed.
        Returns the number of data files recorded.

        It looks for files in format 01.cat 01.dat, 02.cat 02.dat, ... until
        no more pairs are found or it reaches 99.cat 99.dat.
        File priority goes from lowest to highest. Higher-numbered files will
        override entries from lower-numbered files.
        """
        loaded = 0
        data_files = []

        for i in range(1, 100):
            cat_name = '{:02d}.cat'.format(i)
            dat_name = '{:02d}.dat'.format(i)

            cat_path = os.path.join(self.game_root, cat_name)
            dat_path = os.path.join(self.game_root, dat_name)

            if os.path.isfile(cat_path) and os.path.isfile(dat_path):
                data_files.append((cat_path, dat_path))
                loaded += 1
            else:
                break

        self.data_files = data_files + self.data_files

        return loaded

    def _find_directory(self, directories):
        """Tries to return the DirNode for the directory described in the
        directories list. Loads new cat files if needed in order to resolve the
        path.
        Returns None if the path cannot be resolved.

        Arguments:
        directories: list of directory names describing the path to find.
                     E.g. to find the directory 'assets/props/Engines/' pass
                     ['assets', 'props', 'Engines'] as this argument.
        """
        k = self.file_tree

        for directory in directories:
            knext = k.children.get(directory)

            # load new .cat file and retry until the directory is found or no
            # new .cat file can be loaded.
            while not knext and self._load_next_cat_file():
                knext = k.children.get(directory)

            if not knext:
                return None

            k = knext

        return k

    def _find_file(self, directories, filename):
        """Tries to return the CatEntry for the file referenced by the path
        described in the directories list and filename.
        Loads new cat files if needed in order to resolve the path.
        Returns a (CatEntry, DirNode) containing the file entry and parent
        directory node.
        Returns (None, None) if the path cannot be resolved.

        Arguments:
        directories: list of directory names describing the path to the parent
                     directory of the file.
        filename: name of the file to load.

        Example:
        To find the dfile 'assets/props/Engines/generic_engine.xml' pass
        ['assets', 'props', 'Engines'] and 'generic_engine.xml' as arguments.
        """
        directory = self._find_directory(directories)

        if not directory:
            return (None, None)

        entry = directory.files.get(filename)

        # load new .cat file and retry until the directory is found or no new
        # .cat file can be loaded.
        while not entry and self._load_next_cat_file():
            entry = directory.files.get(filename)

        return (entry, directory)

    def open_file(self, path):
        """Open file.
        Returns a binary file-like object.
        """
        parts = split_game_path(path)
        if not path:
            raise ValueError('Empty path {}'.format(path))

        (entry, _) = self._find_file(parts[:-1], parts[-1])
        if not entry:
            raise ValueError('Path {} isn\'t a file'.format(path))

        dat_file = open(entry.dat_path, 'rb')

        return DatGameFile(dat_file, entry.offset, entry.size)

    def file_exists(self, path):
        """Check if file exists."""
        parts = split_game_path(path)

        (entry, _) = self._find_file(parts[:-1], parts[-1])

        return bool(entry)

    def list_files(self, path):
        """List game files under a game directory."""
        parts = split_game_path(path)

        # rebuild full path to remove possible double slashes and to correctly
        # add a slash at the end
        full_path = '/'.join(parts) + '/'

        # must load ALL .cat files to ensure that all the files in the
        # directory are known
        while self._load_next_cat_file():
            pass

        directory = self._find_directory(parts)

        for entry in directory.files.values():
            yield Entry(full_path + entry.name, entry.name)
