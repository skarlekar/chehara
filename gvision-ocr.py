import os
import json
import requests
import base64
import sys
from objectpath import *


def printJson(jsonObject, label):
    """Pretty print JSON document with indentation."""
    print(json.dumps(jsonObject, indent=4, sort_keys=True))


def getBytes(image_url):
    """Given the image_url get the image content and return the bytes."""
    req_for_image = requests.get(image_url, stream=True)
    file_object_from_req = req_for_image.raw
    req_data_bytes = file_object_from_req.read()
    return req_data_bytes


def encodeBytes(file_bytes):
    """Google Vision requires the image data to be sent as base64 encoded bytes"""
    bytestr = base64.b64encode(file_bytes)
    return bytestr


def detectText(image_url):
    """Call Google Vision to detect landmarks in a given image."""
    textDetected = False
    textResponse = None
    ocrText = None
    imageStr = encodeBytes(getBytes(image_url))
    detectionType = "DOCUMENT_TEXT_DETECTION"
    requestJson = {'requests': [{'image': {'content': imageStr}, 'features': [{'type': detectionType}]}]}
    gvision_url = "https://vision.googleapis.com/v1/images:annotate"
    gcp_api_key = os.environ["GCP_API_KEY"]
    myParams = {'key': gcp_api_key}
    response = requests.post(gvision_url, params=myParams, json=requestJson)
    responseCode = response.status_code
    responseHeader = response.headers
    responseJson = response.json()
    print ("Response code: '{}'".format(responseCode))
    #print ("Response header: {}".format(responseHeader))
    #printJson(responseJson, "Response JSON")
    if (responseCode == 200):
        with open('ocr-response.json', 'w') as outfile:
            json.dump(responseJson, outfile)
        print("ocr-response.json written!")
        tree = Tree(responseJson)
        try:
            textResponse = {}
            ocrText = tree.execute("$.responses[fullTextAnnotation].text[0]")
            ocrText = ocrText.encode('utf-8')
            textResponse['textOcr'] = ocrText
            textDetected = True
            print ("Text detected in images is: {}".format(ocrText))
        except StopIteration as e:
            print ("******* Response from Google Vision API did not have any text")
    return textDetected, textResponse


if __name__ == '__main__':
    url = "https://goo.gl/autSFd"
    print "No. of arguments is {}".format(len(sys.argv))
    if len(sys.argv) > 1:
        url = sys.argv[1]
    print(detectText(url))
