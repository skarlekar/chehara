import os
import json
import boto3 as boto
from slackclient import SlackClient
import requests
from datetime import datetime

sns_client = boto.client("sns")
sfn_client = boto.client("stepfunctions")


def printJson(jsonObject, label):
    """Pretty print JSON document with indentation."""
    systime = str(datetime.now())
    print("********************************* {} *********************************".format(label))
    print("--------------------------------- {} ---------------------------------".format(systime))
    print(json.dumps(jsonObject, indent=4, sort_keys=True))
    print("----------------------------------------------------------------------")


def verifyUrl(event):
    """Respond to the challenge by returning the challenge back to Slack"""
    # Create a stock response
    response = {
        "statusCode": 200
    }
    # Get the body
    body = json.loads(event['body'])

    # Find the event type
    event_type = body['type']
    # If event is for verifying URL, return the challenge in the body of the response.
    if event_type == 'url_verification':
        response['body'] = body['challenge']
    return response


def verifyToken(event):
    """Verify that the event is meant for our bot.

    Every event notification contains a verification token sent by Slack.
    Confirm that this verification token belongs to our bot by comparing the
    verification token that was sent with what we know.
    This known verification token is passed to the Lambda through the
    environment variable VERIFICATION_TOKEN.
    """
    verification_token = os.environ['VERIFICATION_TOKEN']
    body = json.loads(event['body'])
    # Verify the token from the request matches what we have. If not, throw an Exception
    token = body['token']
    if token != verification_token:
        raise Exception("Invalid Token")

# def getTopicArn(topic):
#     topicArn = None
#     topics = sns_client.list_topics()["Topics"]
#     for t in topics:
#         if topic in json.dumps(t):
#             topicArn = t["TopicArn"]
#     return topicArn
#
# def publishEvent(body):
#     # Get the Topic arn
#     topicArn = getTopicArn('process_slack_event')
#     payload = json.dumps({'default':json.dumps(body)})
#     # Publish the body on the topic 'publish_event'
#     publish_response = sns_client.publish(TopicArn=topicArn, Message=payload, MessageStructure='json')
#     print("Publish Response: {}".format(json.dumps(publish_response)))


def invokeStepFunction(body):
    """Invoke the StepFunction.

    Invoke the StepFunction with the event data received from the API Gateway.
    """
    stepFnArn = os.environ['STATEMACHINE_ARN']
    stepFnInput = json.dumps(body)
    response = sfn_client.start_execution(stateMachineArn=stepFnArn,
                                            input=stepFnInput)
    print("StepFunction invoke Response: {}".format(response))


def process(event, context):
    """
    Handle URL verifications and other events from Slack.

    This function handles all events from Slack including URL verification. To
    get notified of events happening in the channels that our bot is invited
    to, we will have to specify a URL where Slack should send the events.

    URL Verification: Before using our URL for sending events, Slack will verify if the URL
    belongs to us by sending a challenge. Accept the challenge by sending
    back the challenge token back to Slack.

    Handle Events: Slack expects a 200-OK response to events within three
    seconds. As image detection may run over the three second time limit,
    invoke a step function to farm out detection while returning a 200-OK
    to Slack.

    """
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    printJson(event, "Incoming event")

    # If incoming event is for url verification,  return the challenge in the response.
    response = verifyUrl(event)

    # Verify the token from the request. If it not ours, raise an exception
    verifyToken(event)

    body = json.loads(event['body'])
    slack_event = body['event']
    slack_event_type = slack_event['type']
    slack_event_subtype = slack_event['subtype']

    # Only invoke the StepFunction if the event_type and subtype is of interest
    # to us.
    if (slack_event_subtype) and (slack_event_type == 'message') and (slack_event_subtype == 'file_share'):
        # Invoke the StepFunction
        invokeStepFunction(body)

    printJson(response, "Return Response")
    print("****** Returning response now.")
    return response
