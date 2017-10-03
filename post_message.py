import os
import json
import boto3 as boto
from slackclient import SlackClient
import requests
from datetime import datetime

sns_client = boto.client("sns")

def printJson(jsonObject, label):
    """Pretty print JSON document with indentation."""
    systime = str(datetime.now())
    print("********************************* {} *********************************".format(label))
    print("--------------------------------- {} ---------------------------------".format(systime))
    print(json.dumps(jsonObject, indent=4, sort_keys=True))
    print("----------------------------------------------------------------------")


def getValue(myJson, key):
    """Given a JSON document and a key, return the corresponding value."""
    value = None
    if key in myJson:
        value = myJson[key]
    return value


def postMessage(token, channel, message):
    """Given the Slack access token, post the given message to the Slack channel."""
    print ("Posting the following message in the channel {} : {}".format(channel, message))
    sc = SlackClient(token)
    sc.api_call("chat.postMessage",
                channel= channel,
                text=message)
    print("************((((((Message Posted))))))")


def process(event, context):
    printJson(event, "post_message Input")
    """
    Consolidate the results from the various detectors and post the results
    to the Slack channel.

    The event we get here is a list instead of a dictonary. Each item in the
    list is a dictionary from the parallel lambdas invoked before this step
    was called.
    """

    # Get the access_token and channel from the first dictionary
    listLength = len(event)
    print("************ Number of 'events' in input event is {}".format(listLength))
    if listLength > 0:
        first = event[0]
        message = "Image Detection Results:-------------------------------"
        if "process_events" in first:
            ts = getValue(first["process_events"], "slack_event_ts")
            access_token = getValue(first["process_events"], "slack_access_token")
            channel = getValue(first["process_events"], "slack_event_channel")
        resultsList = []
        for e in event:
            r = e["results"][0]
            resultsList.append(r)
        print("$$$$$$$$$$$$ Length of resultList is {}".format(len(resultsList)))
        if len(resultsList) > 0:
            for result in resultsList:
                message = "{}\n{}".format(message, result)
        message = "{}\n----------- End of Image Detection Results ----------".format(message)
        postMessage(access_token, channel, message)
    return event
