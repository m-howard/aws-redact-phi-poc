import boto3
import os
import uuid
from urllib.parse import unquote_plus

s3 = boto3.client('s3')

def main(event, context):
  for record in event['Records']:
    # get uploaded file name
    bucket = record['s3']['bucket']['name']
    key = unquote_plus(record['s3']['object']['key'])
    print(bucket)
    print(key)

    # create upload and download paths
    tmpkey = key.replace('/', '')
    tmp_download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)

    # Download file
    s3.download_file(bucket, key, tmp_download_path)

    # Upload file
    new_key = key.replace('raw', 'staging')
    print('Copying {} to staging: {}'.format(key, new_key))
    s3.upload_file(tmp_download_path, bucket, new_key)
