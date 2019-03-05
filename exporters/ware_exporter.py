"""Exporter for wares."""

from exporters.helpers import FileLikeProvider, AutoFormatter


def tabular_generator(wares):
    """Generator that produces rows for tabular formats (CSV) from the dict
    given to export_wares. The generated rows don't include all the data about
    the wares.
    """

    # output header
    yield [
        'id',
        'name',
        'factoryname',
        'group',
        'tags',
        'volume',
        'price_min',
        'price_max',
    ]

    for ware_id in sorted(wares.keys()):
        ware = wares[ware_id]

        yield [
            ware_id,
            ware['name'],
            ware['factoryname'],
            ware['group'],
            ' '.join(ware['tags']),
            ware['volume'],
            ware['price_min'],
            ware['price_max']
        ]


def export_wares(wares, destination=None, output_format='csv'):
    """Export the wares dictionary generated by the wares loaded.

    Arguments:
    wares: wares dict generated by the wares loader.
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

    formatter = AutoFormatter(output_format)
    with output as output_file:
        if formatter.is_tabular():
            formatter.output(tabular_generator(wares), output_file)
        elif formatter.is_structured():
            formatter.output(wares, output_file)
        else:
            raise ValueError('Unknown formatter type for format {}'
                             .format(output_format))

    return output.get_return()