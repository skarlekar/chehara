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


def detectLandmark(image_url, access_token):
    """
    Call Google Vision to detect landmarks in a given image.

    Using the given file_url and access_token, get the image data from Slack.
    Using the image data, call Google Vision to recognize landmarks.
    If landmarks were detected, return the response and a boolean representing
    the outcome.
    """
    landmarkDetected = False
    landmarkResponse = {}
    print("############## image_url = {}".format(image_url))
    imageStr = encodeBytes(getBytes(image_url, access_token))
    detectionType = "LANDMARK_DETECTION"
    requestJson = {'requests': [{'image': {'content': imageStr}, 'features': [{'type': detectionType}]}]}
    gvision_url = "https://vision.googleapis.com/v1/images:annotate"
    gcp_api_key = os.environ["GCP_API_KEY"]
    myParams = {'key': gcp_api_key}
    #myHeaders = {'Content-Type': 'application/json'}
    #response = requests.post(gvision_url, headers=myHeaders, params=myParams, json=requestJson)
    response = requests.post(gvision_url, params=myParams, json=requestJson)
    responseCode = response.status_code
    responseHeader = response.headers
    responseJson = response.json()
    print ("Response code: '{}'".format(responseCode))
    print ("Response header: {}".format(responseHeader))
    #printJson(responseJson, "Response JSON")
    if (responseCode == 200):
        tree = Tree(responseJson)
        try:
            landmarkResponse = {}
            landmarkDescription = tree.execute("$.responses[landmarkAnnotations][0][0].description").encode('utf-8')
            landmarkLocation = tree.execute("$.responses[landmarkAnnotations][0][0].locations[0].latLng")
            #print("Landmark Location is: " + json.dumps(landmarkLocation))
            mapUrl = "https://www.google.com/maps/@?api=1&map_action=map&center={},{}&zoom=18&basemap=satellite".format(landmarkLocation["latitude"], landmarkLocation["longitude"])
            landmarkResponse['landmarkDescription'] = landmarkDescription
            landmarkResponse['landmarkLocation'] = landmarkLocation
            landmarkResponse['landmarkMapUrl'] = mapUrl
            landmarkDetected = True
            landmarkResponse['landmarkDetected'] = True
        except StopIteration as e:
            print ("******* Response from Google Vision API did not have any landmark")
    return landmarkDetected, landmarkResponse


# def addLandmarkInfo2(event):
#     value = 'No landmarks detected in the uploaded picture'
#     event.setdefault('results', [])
#     event['results'].append(value)
#     return event


def addLandmarkInfo(event):
    """Enrich the input event with the result of landmark recogniton."""
    value = 'No landmarks detected in the uploaded picture'
    if "detect_landmark" in event:
        if "landmark_detected" in event["detect_landmark"]:
            landmark_detected = event["detect_landmark"]["landmark_detected"]
            if landmark_detected:
                landmarkDescription = event["detect_landmark"]["landmarkDescription"]
                landmarkMapUrl = event["detect_landmark"]["landmarkMapUrl"]
                print ("Landmark detected in images is: {}".format(landmarkDescription))
                print ("Landmark map is: {}".format(landmarkMapUrl))
                value = "Detected the following landmark in the picture \n"
                value = "{} Landmark: {} \n".format(value, landmarkDescription)
                value = "{} Map: {} \n".format(value, landmarkMapUrl)
    event.setdefault('results', [])
    event['results'].append(value)
    return event

def process(event, context):
    """
    Process the given image to detect landmarks by invoking Google Vision.

    Extract the image url, and access token from the enriched event. Use the
    access token to get the image data from Slack. Invoke Google Vision
    to detect landmarks. If landmarks are found, enrich the input event
    with information about the landmarks found in the picture.
    """
    body = event
    printJson(body, "detect_landmark Input")
    if "process_events" in event:
        file_url = getValue(event["process_events"], "slack_event_file_url")
        access_token = getValue(event["process_events"], "slack_access_token")
        print("Detecting Landmarks")
        landmark_detected, detect_landmark_response = detectLandmark(file_url, access_token)
        print("Landmark Detection response: Detected = {}, Results = {} ".format(landmark_detected, detect_landmark_response))
        event['detect_landmark'] = detect_landmark_response
        event['detect_landmark']['landmark_detected'] = landmark_detected
    addLandmarkInfo(event)
    print("****** Done processing event.")
    return event
