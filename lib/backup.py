#!/usr/bin/env python

import os
import time
import glob
import tarfile
import datetime

import configparser

from lib import aws


def get_config(config):

    """Create ConfigParcer object with configuration file.
       File can be passed with -c."""

    parser = configparser.ConfigParser()

    if len(parser.read(config)) == 0:
        raise Exception('ERROR: No config file {} found!'.format(config))

    return parser


class NotTodayException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        print (message)


def isruntoday(item, item_params):

    """Will check for item's `runon` option days
    and compare to today's day name ("monday" etc).
    Will raize the NotTodayException if today's day name missing in item's `runon` list."""

    days = {'Monday': 'mo',
            'Tuesday': 'tu',
            'Wednesday': 'we',
            'Thursday': 'th',
            'Friday': 'fr',
            'Saturday': 'sa',
            'Sunday': 'su'}

    # weekdays to run job
    runon = item_params['runon']

    # print ('Today: {};\nRunOn: {};'.format(days.get(datetime.datetime.now().strftime('%A')), runon))

    # i.e. days.get('Monday') - will return 'mo' if exist in the `runon` list
    if days.get(datetime.datetime.now().strftime('%A')) in runon:
        print ('Backing up item {}.'.format(item))
    else:
        raise NotTodayException('Item {} does not marked to be copied today.'.format(item))


def set_params(item, parser):

    """Set parameters for each ITEM in configuration file
       excluding "defaults" item.
       Example:
       {'source': "'/home/setevoy/Dropbox/KeyPass/'",
       'destination': "'/home/setevoy/Backups/KeyPass/'", 'type': "'file'", 'store': "'s3'"}"""

    params = dict.fromkeys(['accesskey',
                            'secretkey',
                            'datatype',
                            'bkptype',
                            'source',
                            'destination',
                            'store',
                            'period',
                            'bucket',
                            'droponpush',
                            'fullretain',
                            'incretain',
                            'runon'])

    for param in params.keys():

        # Checking: KeyPass, param: source
        # print ('Checking: {}, param: {}'.format(item, param))

        try:
            params[param] = (parser.get(item, param))
            # param source, value '/home/setevoy/Dropbox/KeyPass/'
            # print ('param {}, value {}'.format(param, params[param]))
        except configparser.NoOptionError:

            # print ('{} not found for {}, checking the "defaults"...'.format(param, item))

            try:
                params[param] = (parser.get('defaults', param))
                # print ('param {}, value {}'.format(param, params[param]))
            except configparser.NoOptionError:
                raise Exception('ERROR: '
                                'No "{}" found neither in "{}" nor in the "defaults" items! Exit.'.format(param, item))

    # if keys not found neither in the "defaults" not in the "itemname" sections
    # try catch it from environment variables (AWS method)
    # if s3 will be used and keys is empty - exception will be handled by aws module
    if not params['accesskey'].strip('\'') and not params['secretkey'].strip('\''):
        try:
            params['accesskey'] = os.environ['AWS_ACCESS_KEY_ID']
            params['secretkey'] = os.environ['AWS_SECRET_ACCESS_KEY']
        except KeyError:
            pass

    return params


def cleanup_local(item_params):

    """Remove outdated backup files from the "destination" parameter."""

    fullretain = item_params['fullretain'].strip('\'')
    incretain = item_params['incretain'].strip('\'')

    dst = item_params['destination'].strip('\'')

    # full backups list
    f_files = glob.glob1(dst, '*_full_*')
    # incremental backups count
    i_files = glob.glob1(dst, '*_inc_*')

    # work with files directly
    os.chdir(dst)

    f_files = sorted(f_files, key=os.path.getctime)
    i_files = sorted(i_files, key=os.path.getctime)

    for f in f_files[0:-int(fullretain)]:
        os.remove(f)

    for i in i_files[0:-int(incretain)]:
        os.remove(i)

    # print ('Existing backups in {}: {}'.format(dst, os.listdir()))


def file_full_backup(item, item_params):

    """Create TAR.GZ file with all data from item's "source" """

    src = item_params['source'].strip('\'')
    dst = item_params['destination'].strip('\'')

    # 2016_12_29_17_07_31
    timestamp = time.strftime('_%Y_%m_%d_%H_%M_%S')
    # KeyPass2016_12_29_17_08_02.tar.gz
    bkpname = item + '_full' + timestamp + '.tar.gz'
    outfile = dst + bkpname

    if not os.path.isdir(dst):
        os.makedirs(dst)

    try:
        with tarfile.open(outfile, "w:gz") as tar:
            tar.add(src)
    except FileNotFoundError as e:
        print ('ERROR: {}. Skip.'.format(e))

    # SAVE here
    # 'outfile' here == 'src' for s3push
    if item_params['store'] == "'s3'":
        aws.s3push(outfile, bkpname, item_params)
        # dst here == src for S3
        aws.s3clean(dst, item, item_params)

    # DROP here
    if item_params['store'] == "'local'":
        cleanup_local(item_params)


def file_inc_backup(item, item_params):

    """Create TAR.GZ file with data from item's "source" changed during last "period"."""

    # https://rtfm.co.ua/python-skript-inkrementalnogo-ili-polnogo-bekapa-fajlov/
    now = time.time()
    # 24 hours * 3600 secons == 86400 seconds
    # cutoff = 3600 // 1 hour
    cutoff = int(item_params['period']) * 3600

    src = item_params['source'].strip('\'')
    dst = item_params['destination'].strip('\'')

    # 2016_12_29_17_07_31
    timestamp = time.strftime('_%Y_%m_%d_%H_%M_%S')
    # KeyPass2016_12_29_17_08_02.tar.gz
    bkpname = item + '_inc' + timestamp + '.tar.gz'
    outfile = dst + bkpname

    if not os.path.isdir(dst):
        os.makedirs(dst)

    try:

        with tarfile.open(outfile, "w:gz") as tar:
            for root, dirs, files in os.walk(src, followlinks=True):
                for f in files:
                    file_to_backup = os.path.join(root, f)
                    try:
                        # to test - os.path.getmtime()
                        filemodtime = os.stat(file_to_backup).st_mtime
                        if now - filemodtime < cutoff:
                            # print ('Adding file: {}'.format(file_to_backup))
                            tar.add(file_to_backup)
                            # print ('File modified: {}'.format(time.ctime(os.path.getmtime(file_to_backup))))
                    except OSError as error:
                        print ('ERROR: {}'.format(error))
    except FileNotFoundError as e:
        print ('ERROR: {}. Skip.'.format(e))

    # SAVE here
    # 'outfile' here == 'src' for s3push
    if item_params['store'] == "'s3'":
        aws.s3push(outfile, bkpname, item_params)
        # dst here == src for S3
        aws.s3clean(dst, item, item_params)

    # DROP here
    if item_params['store'] == "'local'":
        cleanup_local(item_params)


def db_backup():

    """To do later."""

    print ('dbs')


def backup(config):

    """Run backup through an items (sections) in configuration file."""

    parser = get_config(config)

    for item in parser.sections():

        item_params = set_params(item, parser)

        while True:

            if item != 'defaults':

                print ('\nChecking: {} backup.'.format(item))

                try:
                    isruntoday(item, item_params)
                except NotTodayException:
                    # print ('{} - not today!'.format(item))
                    break

                if item_params['datatype'] == "'file'":
                    if item_params['bkptype'] == "'full'":
                        # print ('\nCreating item {} {} backup.\n'.format(item, item_params['bkptype']))
                        # for param in item_params:
                        #     print ('Parameters: {}: {}'.format(param, item_params[param]))
                        file_full_backup(item, item_params)
                        break
                    elif item_params['bkptype'] == "'inc'":
                        # print ('\nCreating item {} {} backup.\n'.format(item, item_params['bkptype']))
                        # for param in item_params:
                        #    print ('Parameters: {}: {}'.format(param, item_params[param]))
                        file_inc_backup(item, item_params)
                        break
                    else:
                        raise Exception('ERROR: unknown backup type (full/inc).'
                                        ' Please - check {}.'.format(config))
                elif item_params['type'] == "'db'":
                    db_backup()
                    break
                else:
                    raise Exception(
                        'ERROR: Unknown data type for the {}! Exit.'.format(item))
            else:
                break
