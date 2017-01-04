#!/usr/bin/env python

import os
import shutil

import boto3
import botocore


def s3auth(accesskey, secretkey):

    """Create Boto3 authentificated object."""

    s3client = boto3.client('s3',
        aws_access_key_id=accesskey,
        aws_secret_access_key=secretkey,
    )

    return s3client


def s3push(src, bkpname, item_params):

    """Save an "src" to the "bucket" (from config) with key name as "bkpname"."""

    accesskey = item_params['accesskey'].strip('\'')
    secretkey = item_params['secretkey'].strip('\'')
    droponpush = item_params['droponpush'].strip('\'')
    y = 1, "yes", "true", "True"
    # n = 0, "no", "false", "False"

    # we can't proceed with S3 upload with authentication
    assert accesskey
    assert secretkey

    s3client = s3auth(accesskey, secretkey)

    bucket = item_params['bucket'].strip('\'')
    dst = item_params['destination'].strip('\'')

    s3client.upload_file(src, bucket, dst + bkpname)

    try:
        # check if file was uploaded
        s3client.get_object(Bucket=bucket, Key=dst + bkpname)
        print ('Item {} created in {}.'.format(dst + bkpname, bucket))
        if droponpush in y:
            os.remove(src)
            if not os.path.isfile(src):
                print ('Local copy {} deleted.'.format(src))
            shutil.rmtree(dst, ignore_errors=True)
            if not os.path.isdir(dst):
                print ('Local copy {} deleted.'.format(dst))
    except botocore.exceptions.ClientError as e:
        print ('ERROR: {}'.format(e))
        # check here later for raise
        exit(1)


def s3clean(src, item, item_params):

    """later"""

    accesskey = item_params['accesskey'].strip('\'')
    secretkey = item_params['secretkey'].strip('\'')

    if item_params['bkptype'] == "'full'":
        retain = item_params['fullretain'].strip('\'')
    elif item_params['bkptype'] == "'inc'":
        retain = item_params['incretain'].strip('\'')

    # we can't proceed with S3 upload with authentication
    assert accesskey
    assert secretkey

    bucket = item_params['bucket'].strip('\'')

    s3client = s3auth(accesskey, secretkey)

    # select all backups starting with Prefix
    item_backups = s3client.list_objects(Bucket=bucket, Prefix=src + item)
    # select Content dictionary from item_backups
    content = item_backups.get('Contents')

    # backups to be dropped will be added here
    to_drop = []

    # only if existing backups number greater then `retain`
    if len(content) > int(retain):
        # add to the `to_drop` list everything, excluding first len(retain) items
        # `content` list have items sorted by names
        # as each starts with an item's name (which is same) and have timestamp (which will differ)
        # - they will be sorted by time
        # i.e.:
        # KeyPass / Full / KeyPassFullS3Sunday_full_2017_01_04_16_55_37.tar.gz
        # KeyPass / Full / KeyPassFullS3Sunday_full_2017_01_04_17_35_19.tar.gz
        # KeyPass / Full / KeyPassFullS3Sunday_full_2017_01_04_17_36_04.tar.gz
        # KeyPass / Full / KeyPassFullS3Sunday_full_2017_01_04_17_36_23.tar.gz
        for i in content[:-int(retain)]:
            to_drop.append(i)

    for item_to_delete in to_drop:
        print ('Deleting: {}'.format(item_to_delete.get('Key')))
        s3client.delete_object(Bucket=bucket, Key=item_to_delete.get('Key'))



