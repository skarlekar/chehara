import os
import json
import boto3 as boto
from slackclient import SlackClient
import requests
from datetime import datetime


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

    print("getBytes Inputs: file_url={}, access_token={}".format(image_url, access_token))
    authorization = "Bearer {}".format(access_token)
    req_for_image = requests.get(image_url, stream=True, headers={'Authorization': authorization})
    file_object_from_req = req_for_image.raw
    req_data_bytes = file_object_from_req.read()
    print("getBytes completed")
    return req_data_bytes


def detectCelebrity(file_url, access_token):
    """
    Call AWS Rekognition to detect celebrities in a given image.

    Using the given file_url and access_token, get the image data from Slack.
    Using the image data, call AWS Rekognition to recognize celebrities.
    If celebrities were detected, return the response and a boolean representing
    the outcome.
    """
    print("detectCelebrity Inputs: file_url={}, access_token={}".format(file_url, access_token))
    unrecognized_detected = False
    celebrity_detected = False
    client = boto.client('rekognition')
    response = {}
    errored = False
    # An InvalidImageException will be raised if Rekognition does not support the
    # given image type. For instance, animated GIF etc.
    try:
        image_bytes = getBytes(file_url, access_token)
        print("-------- Calling Rekognition....")
        response = client.recognize_celebrities(Image={'Bytes': image_bytes})
        errored = False
    except Exception as e:
        errored = True
        print ("Following error was raised:")
        print (e)
        print ("----------------------------")
        response = {}

    if (errored is False) and (response is not None):
        if len(response['CelebrityFaces']) > 0:
            celebrity_detected = True
        if len(response['UnrecognizedFaces']) > 0:
            unrecognized_detected = True
            del response['UnrecognizedFaces']
        if (celebrity_detected):
            for celebrity in response['CelebrityFaces']:
                del celebrity['Face']
        del response['ResponseMetadata']

    printJson(response, "detect_face Response")
    return celebrity_detected, response


def getValue(myJson, key):
    """Given a JSON document and a key, return the corresponding value."""
    value = None
    if key in myJson:
        value = myJson[key]
    return value


def addCelebrityInfo(event):
    """ Enrich the input event with the result of celebrity recogniton."""
    value = 'No celebrities detected in the uploaded picture'
    if "detect_celebrity" in event:
        if "celebrity_detected" in event["detect_celebrity"]:
            celebrity_detected = event["detect_celebrity"]["celebrity_detected"]
            if celebrity_detected:
                cfaces = event["detect_celebrity"]["CelebrityFaces"]
                printJson(cfaces, "CelebrityFaces")
                value = "Detected {} celebrities in the picture. \n".format(len(cfaces))
                for cface in cfaces:
                    name = getValue(cface, 'Name')
                    confidence = getValue(cface, 'MatchConfidence')
                    urls = getValue(cface, 'Urls')
                    url = ''
                    if (urls):
                        if len(urls) > 0:
                            url = urls[0]
                    value = "{} Name: {}, Match Confidence: {}, More Information: http://{} \n".format(value, name, confidence, url)
    event.setdefault('results', [])
    event['results'].append(value)
    return event


def process(event, context):
    """
    Process the given image to detect celebrities by invoking AWS Rekognition.

    Extract the image url, and access token from the enriched event. Use the
    access token to get the image data from Slack. Invoke AWS Rekognition
    to detect celebrities. If celebrities are found, enrich the input event
    with information about the celebrities found in the picture.
    """
    printJson(event, "detect_celebrity Input")
    if "process_events" in event:
        file_url = getValue(event["process_events"], "slack_event_file_url")
        access_token = getValue(event["process_events"], "slack_access_token")
        print("Detecting celebrities")
        celebrity_detected, detect_celebrity_response = detectCelebrity(file_url, access_token)
        print("Celebrity Detection response: Detected = {}, Results = {} ".format(celebrity_detected, detect_celebrity_response))
        event['detect_celebrity'] = detect_celebrity_response
        event['detect_celebrity']['celebrity_detected'] = celebrity_detected
        addCelebrityInfo(event)

    printJson(event, "Return this event downstream")
    print("****** Done processing event.")
    return event
