import boto3
import os
import sys
import uuid
import functools
import PIL.Image
from urllib.parse import unquote_plus
from trp import Document
from PIL import Image, ImageDraw

s3 = boto3.client('s3')
textract = boto3.client('textract')
comprehend = boto3.client('comprehendmedical')

def draw_document_boxes(document, identified_text, save_path, fill=False):
  for text in identified_text:
    draw = ImageDraw.Draw(document)
    if fill:
      draw.rectangle(text["BoundingBox"], fill='White')
    else:
      draw.rectangle(text["BoundingBox"], width=1, outline='White')
  document.save(save_path)

def identify_text(document, textract_data):
  result = []
  width, height = document.size
  for block in textract_data["Blocks"]:
    if block["BlockType"] == "WORD" and block["Confidence"] >= 90.0:
      text = {}
      text["Value"] = block["Text"]
      geometry = block["Geometry"]["BoundingBox"]
      x0 = geometry["Left"] * width
      y0 = geometry["Top"] * height
      x1 = x0 + geometry["Width"] * width
      y1 = y0 + geometry["Height"] * height
      text["BoundingBox"] = [x0, y0, x1, y1]
      text["phi"] = False
      result.append(text)
  return result

def comprehend_phi(med_text):
  phi = []
  for entity in med_text:
    if entity["Category"] == "PROTECTED_HEALTH_INFORMATION":
      phi.extend(entity["Text"].split())
  return phi

def identify_phi(identified_text, comprehend_phi_text):
  result = []
  for phi_text in comprehend_phi_text:
    for i, text in enumerate(identified_text):
      if phi_text == text["Value"] and not text["phi"]:
        result.append(text)
        identified_text[i]["phi"] = True
        continue
  return result

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
    tmp_indentified_path = '/tmp/identified-{}'.format(tmpkey)
    tmp_redacted_path = '/tmp/redacted-{}'.format(tmpkey)

    # Download file
    s3.download_file(bucket, key, tmp_download_path)

    # Analyze document with textract
    textract_response = textract.analyze_document(
      Document={
        'S3Object': {
          'Bucket': bucket,
          'Name': key
        }
      },
      FeatureTypes=['TABLES', 'FORMS']
    )
    print(textract_response)

    # Convert data to new identified text format
    identified_text = identify_text(Image.open(tmp_download_path), textract_response)

    # Create new document with identified text
    draw_document_boxes(Image.open(tmp_download_path), identified_text, tmp_indentified_path)
    s3.upload_file(tmp_indentified_path, bucket, key.replace('staging', 'identified'))

    # Prepare for comprehend
    paragraph = functools.reduce(
      lambda a,b : ' '.join([a, b]),
      list(map(lambda x: x["Value"], identified_text))
    )

    # Analyze text with comprehend medical
    comprehend_response =  comprehend.detect_entities(Text=paragraph)
    print(comprehend_response)

    # Create new document with redacted text
    comprehend_phi_text = comprehend_phi(comprehend_response["Entities"])
    print(comprehend_phi_text)
    identified_phi = identify_phi(identified_text, comprehend_phi_text)
    print(identified_phi)
    draw_document_boxes(Image.open(tmp_download_path), identified_phi, tmp_redacted_path, fill=True)
    s3.upload_file(tmp_redacted_path, bucket, key.replace('staging', 'redacted'))
