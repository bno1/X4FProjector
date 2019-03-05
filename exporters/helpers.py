"""Helper for exporters."""

import io


FORMATTER_EXTENSIONS = {
    'csv': 'csv',
    'json': 'json',
    'yaml': 'yaml',
    'pyyaml': 'yaml',
}


class FileLikeProvider:
    """Class that produces a file-like object for different kinds of outputs.
    The purpose is to relieve exporters of handling different kinds of outputs.

    Supported output types (see doc of __init__):
    - to string
    - to file object
    - to file path (takes care of opening the file)

    Usage:
        # destination = None or string or other
        file_provider = FileLikeProvider(destination)
        with file_provider as file_object:
            file_object.write('my data')

        # if destination is None
        data = file_provider.get_return()
    """

    def __init__(self, destination):
        """Initializes the FileLikeProvider.

        Arguments:
        destination: destination for the output. Possible values:
                     - None: destination is a string. __enter__ will return a
                             StringIO object. get_return will return the
                             string with the written content.
                     - string: interpreted as a path to a file. __enter__ will
                               return the opened file. get_return will return
                               None.
                     - anything else: __enter__ will return this object.
                                get_return will return None.
        """
        self.destination = destination
        self.file_object = None
        self.ret = None

    def __enter__(self):
        """Opens/creates the file-like object and returns it."""
        if not self.destination:
            self.file_object = io.StringIO(newline='')
        elif isinstance(self.destination, str):
            self.file_object = open(self.destination, 'w', newline='')
        else:
            self.file_object = self.destination

        return self.file_object.__enter__()

    def __exit__(self, *args):
        """Closes the file-like object.
        Will save the contents to self.ret in certain cases (like string
        output).
        """
        if not self.destination:
            self.ret = self.file_object.getvalue()

        self.file_object.__exit__(*args)

    def get_return(self):
        """Return result after finishing writing to the provided file-like."""
        return self.ret


class AutoFormatter:
    """Prints generic data to different output formats.
    The purpose is to relieve exporters from handling different kinds of output
    formats.
    Generic data means python lists, dictionaries, strings, numbers, None, and
    derivatives.

    Format kinds:
    - Tabular: expects a list of lists (table) of string/numeric/None values.
    - Structured: expects a list/dictionary/string/numberic/None. Basically
                  anything that has a structure similar to JSON or YAML files.

    Supported formats:
    - CSV: tabular.
    - JSON: structured.
    - PYYAML: structured, uses the PyYAML library.
    - YAML: structured, automatically picks whatever yaml library available.
    """

    # TODO add ruamel.yaml

    def __init__(self, output_format):
        """Initializes the formatter.

        Arguments:
        output_format: output format to use. See Supported Formats for a list
                       of available formats. Case insensitive.
        """
        self.output_format = output_format.lower().strip()

    def is_tabular(self):
        """Is the output tabular?"""
        return self.output_format in ['csv']

    def is_structured(self):
        """Is the output format structured?"""
        return self.output_format in [
            'json', 'yaml', 'pyyaml',
        ]

    @staticmethod
    def get_extension(output_format):
        """Return the default file extension for an output format."""
        return FORMATTER_EXTENSIONS[output_format]

    def output(self, data, file_object):
        """Outputs the data to a the file_object in the format given at
        initialization.

        Arguments:
        data: data to output. See The class documentation for details.
        file_object: file-like object used for writing the output.
        """
        output_format = self.output_format

        if output_format == 'csv':
            import csv

            writer = csv.writer(file_object)

            for row in data:
                writer.writerow(row)

            return

        if output_format == 'json':
            import json

            json.dump(data, file_object, indent='  ', sort_keys=True)
            return

        if output_format == 'yaml':
            import importlib

            if importlib.util.find_spec('yaml') is not None:
                output_format = 'pyyaml'
            else:
                raise ImportError('Cannot find a supported yaml module')

        if output_format == 'pyyaml':
            import yaml

            yaml.dump(data, file_object, indent=2, default_flow_style=False)
            return

        raise ValueError('Unsupported output format: {}'.format(output_format))
