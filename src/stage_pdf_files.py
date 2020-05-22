import boto3
import os
import sys
import uuid
from urllib.parse import unquote_plus
from PyPDF2 import PdfFileWriter, PdfFileReader # https://stackoverflow.com/questions/490195/split-a-multi-page-pdf-file-into-multiple-pdf-files-with-python

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
    tmp_split_path = '/tmp/split'
    os.mkdir(tmp_split_path)

    # Download file
    s3.download_file(bucket, key, tmp_download_path)

    # Split PDF and upload new docs to staging area
    document = PdfFileReader(open(tmp_download_path, "rb"))
    for i in range(document.numPages):
      output = PdfFileWriter()
      output.addPage(document.getPage(i))
      tmp_page_path = '{}/pdf-{}-{}'.format(tmp_split_path, i, tmpkey)
      with open(tmp_page_path, "wb") as outputStream:
        output.write(outputStream)
      new_key = key.replace('.pdf', '/{}.pdf'.format(i))
      s3.upload_file(tmp_page_path, bucket, new_key.replace('raw', 'staging'))
