#!/usr/bin/env python

"""Personal backup script"""

import argparse

from lib import backup

__author__ = "Arseny Zinchenko"
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Arseny Zinchenko"
__email__ = "1th@setevoy.kiev.ua"
__status__ = "Development"


def getopts():

    """Use '-c' to specify non-default configuration file.
    #ToDo: options to overwrite options in config file."""

    parser = argparse.ArgumentParser()

    parser.add_argument('-c',
                              '--config',
                              action='store',
                              default='conf/mybackup.ini',
                              help='Path to the config file. Default - conf/mybackup.ini')

    parser.add_argument('-A',
                              '--accesskey',
                              action='store',
                              required=False,
                              help='aws_access_key_id')

    parser.add_argument('-S',
                              '--secretkey',
                              action='store',
                              required=False,
                              help='aws_access_key_id')

    return parser.parse_args()


if __name__ == '__main__':

    options = vars(getopts())
    config = (options['config'])

    backup.backup(config)
