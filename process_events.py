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


def getTeam(team_id):
    """Given a team id, lookup the team data from DynamoDB."""
    table_name = os.environ['SLACK_TEAMS']
    dynamodb = boto.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table_key = {'team_id': team_id}
    result = table.get_item(Key=table_key)['Item']
    return result


def getAccessToken(team):
    """Extract the access token from the team data given."""
    access_token = None
    if team:
        access_token = team['access_token']
    return access_token


def process(event, context):
    """
    Process the incoming Slack event.

    If the incoming event is a file_share event and the file shared is an image,
    lookup the team data from the database based on the team id in the event.
    Enrich the event with a new object to include the access_token and other
    details and return the information. StepFunction will take this enriched
    event to the next layer of Lambda functions to process.
    """
    # Event comes as a JSON. No need to convert.
    body = event
    printJson(body, "process_events Input")
    team_id = body['team_id']
    team = getTeam(team_id)
    access_token = getAccessToken(team)
    slack_event = body['event']
    printJson(slack_event, "slack_event")
    slack_event_type = slack_event['type']
    slack_event_channel = slack_event['channel']
    slack_event_subtype = slack_event['subtype']
    slack_event_ts = slack_event['ts']
    slack_event_username = slack_event['username']
    slack_event_file = None
    celebrity_detected = False
    celebs = None
    if (slack_event_subtype) and (slack_event_type == 'message') and (slack_event_subtype == 'file_share'):
        slack_event_file = slack_event['file']
        file_type = slack_event_file['filetype']
        if file_type == 'jpg' or file_type == 'png':
            file_url = slack_event_file['url_private']
            process_events = {
                'team_id': team_id,
                'team': team,
                'slack_access_token': access_token,
                'slack_event_type': slack_event_type,
                'slack_event_channel': slack_event_channel,
                'slack_event_subtype': slack_event_subtype,
                'slack_event_ts': slack_event_ts,
                'slack_event_username': slack_event_username,
                'slack_event_filetype': file_type,
                'slack_event_file_url': file_url
            }
            event['process_events'] = process_events
    printJson(event, "Return this event downstream")
    print("****** Done with process_events")
    return event
