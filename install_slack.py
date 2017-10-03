import os
import json
import boto3 as boto
from slackclient import SlackClient
import requests


def pp_json(json_thing, sort=True, indents=4):
    """Pretty print JSON document with indentation."""
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


def getCode(event):
    """Get the authorization code from the event."""
    print(json.dumps(event))
    auth_code = None
    if event and event['queryStringParameters'] and event['queryStringParameters']['code']:
        auth_code = event['queryStringParameters']['code']
    return auth_code


def getAuthorization(auth_code):
    """
    Get the OAuth token and team data from Slack.

    Use the temporary authorization code to get the OAuth token and team
    information from Slack.
    """
    auth_response = None
    # Get the client_id and client_secret from the Lambda environment variables
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    # An empty string is a valid token for this request
    sc = SlackClient("")
    # Request the auth tokens from Slack
    auth_response = sc.api_call(
        "oauth.access", client_id=client_id, client_secret=client_secret,
        code=auth_code)
    return auth_response


def saveResponse(auth_response):
    """
    Store the team information to the database.

    Use this function to store the authorization response from Slack.
    """
    table_name = os.environ['SLACK_TEAMS']
    dynamodb = boto.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(Item=auth_response)
    print("auth_response written to table: {}".format(table_name))


def process(event, context):
    """
    Slackbot installer.

    This function is called when a user installs our slackbot in their
    workspace. Slack sends a temporary code that should be used to get the
    slack authorization token. This authorization token is then stored
    and should be used in future calls to Slack API.

    A success or error response should be a 302 HTTP code to redirect the user
    to a HTML page.
    """
    success_response = {
        "statusCode": 302,
        "headers": {
            "Location": os.environ['INSTALL_SUCCESS_URL']
        }
    }
    error_response = {
        "statusCode": 302,
        "headers": {
            "Location": os.environ['INSTALL_ERROR_URL']
        }
    }
    response = success_response
    try:
        auth_code = getCode(event)
        auth_response = getAuthorization(auth_code)
        saveResponse(auth_response)
        print("************************* Code = {}".format(auth_code))
        print("***************************** auth_response :")
        print(json.dumps(auth_response))
    except Exception as e:
        print ("Following error was raised:")
        print (e)
        print ("----------------------------")
        response = error_response

    print("****** Returning the following from Lambda")
    print(json.dumps(response))
    print("------------------------------------------")
    return response
