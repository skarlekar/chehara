import os
import json
import boto3 as boto
from slackclient import SlackClient
import requests
from datetime import datetime
import base64
import sys
from objectpath import *


def printJson(jsonObject, label):
    """Pretty print JSON document with indentation."""
    systime = str(datetime.now())
    print("********************************* {} *********************************".format(label))
    print("--------------------------------- {} ---------------------------------".format(systime))
    print(json.dumps(jsonObject, indent=4, sort_keys=True))
    print("----------------------------------------------------------------------")


def getBytes(image_url, access_token):
    """
    Given the image_url and access_token, call Slack to get the image content.

    As we will be using the private_url, Slack requires the access_token to
    retrieve the image. Send the access_token as Bearer token to get the image
    content as bytes. Return the bytes.
    """
    authorization = "Bearer {}".format(access_token)
    #req_for_image = requests.get(image_url, stream=True, headers={'Authorization': 'Bearer xoxp-245911183507-246125492149-245501091713-4142df0229f805ccd18d1c57d985c718'})
    req_for_image = requests.get(image_url, stream=True, headers={'Authorization': authorization})
    file_object_from_req = req_for_image.raw
    req_data_bytes = file_object_from_req.read()
    return req_data_bytes


def encodeBytes(file_bytes):
    """Google Vision requires the image data to be sent as base64 encoded bytes"""
    bytestr = base64.b64encode(file_bytes)
    return bytestr


def getValue(myJson, key):
    """Given a JSON document and a key, return the corresponding value."""
    value = None
    if key in myJson:
        value = myJson[key]
    return value


def detectText(image_url, access_token):
    """
    Call Google Vision to detect text in a given image.

    Using the given file_url and access_token, get the image data from Slack.
    Using the image data, call Google Vision to recognize text.
    If text was detected, return the response and a boolean representing
    the outcome.
    """
    textDetected = False
    textResponse = {}
    ocrText = None
    imageStr = encodeBytes(getBytes(image_url, access_token))
    detectionType = "DOCUMENT_TEXT_DETECTION"
    requestJson = {'requests': [{'image': {'content': imageStr}, 'features': [{'type': detectionType}]}]}
    gvision_url = "https://vision.googleapis.com/v1/images:annotate"
    gcp_api_key = os.environ["GCP_API_KEY"]
    myParams = {'key': gcp_api_key}
    response = requests.post(gvision_url, params=myParams, json=requestJson)
    responseCode = response.status_code
    responseHeader = response.headers
    responseJson = response.json()
    if (responseCode == 200):
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


def addTextInfo(event):
    """Enrich the input event with the result of text recogniton."""
    value = 'No text detected in the uploaded picture'
    if "detect_text" in event:
        if "text_detected" in event["detect_text"]:
            text_detected = event["detect_text"]["text_detected"]
            if text_detected:
                text = event["detect_text"]["textOcr"]
                print ("Text detected in images is: {}".format(text))
                value = "Detected the following text in the picture \n"
                value = "{} Text: \n{} \n".format(value, text)
    event.setdefault('results', [])
    event['results'].append(value)
    return event

def process(event, context):
    """
    Process the given image to detect text by invoking Google Vision.

    Extract the image url, and access token from the enriched event. Use the
    access token to get the image data from Slack. Invoke Google Vision
    to detect text. If text is found, enrich the input event
    with information about the text found in the picture.
    """
    # Event comes as a JSON. No need to convert.
    body = event
    printJson(body, "detect_text Input")
    if "process_events" in event:
        file_url = getValue(event["process_events"], "slack_event_file_url")
        access_token = getValue(event["process_events"], "slack_access_token")
        print("Detecting text")
        text_detected, detect_text_response = detectText(file_url, access_token)
        print("Text Detection response: Detected = {}, Results = {} ".format(text_detected, detect_text_response))
        event['detect_text'] = detect_text_response
        event['detect_text']['text_detected'] = text_detected
    addTextInfo(event)
    print("****** Done processing event.")
    return event
