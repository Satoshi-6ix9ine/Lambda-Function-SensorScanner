# -*- coding: utf-8 -*-
import time
import urllib
import urllib2
import boto3
import json
import os

from base64 import b64decode
from urlparse import parse_qs
from collections import namedtuple
from datetime import datetime, timedelta

ENCRYPTED_SLACK_URL = os.environ['slackWebhookUrl']
ENCRYPTED_LOOOP_API_KEY = os.environ['looopApiKey']
ENCRYPTED_API_URL = os.environ['apiUrl']

# SLACK_URL = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_SLACK_URL))['Plaintext']
# LOOOP_API_KEY = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_LOOOP_API_KEY))['Plaintext']
# API_URL = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_API_URL))['Plaintext']

SLACK_URL = 'https://hooks.slack.com/services/.decrypt(CiphertextBlob=b64decode(ENCRYPTED_SLACK_URL))
LOOOP_API_KEY = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_LOOOP_API_KEY))
API_URL = 'https://sensor-checkin-service.api.prod.looop.in'

Response = namedtuple('Response', 'status_code, json')

class SimpleRequests(object):
    @staticmethod
    def post(url, data, params=None):
        params = params or {}
        encoded = urllib.urlencode(params)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(
            url + '?' + encoded,
            data=json.dumps(data)
        )
        request.add_header('Content-Type', 'application/json')
        request.get_method = lambda: 'POST'
        try:
            resp = opener.open(request)
            resp_json = json.loads('{{"data": "{0}"}}'.format(resp.fp.read()))
        except ValueError:
            resp_json = None

        response = Response(
            resp.code,
            resp_json
        )
        return response


    @staticmethod
    def get(url, headers=None):
        headers = headers or {}
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url)
        for name, value in headers.iteritems():
            request.add_header(name, value)
        read = opener.open(request).fp.read()
        return json.loads(read)


class ApiClient:
    def __init__(self, api_url):
        self.request_client = SimpleRequests
        self.api_url = api_url

    def _get_headers(self):
        return {
            "x-looop-api-key": LOOOP_API_KEY,
            "Content-Type": "application/json"
        }

    def _make_get_call(self, endpoint):
        return self.request_client.get(
            self.api_url + endpoint,
            headers=self._get_headers()
        )

    def get_notify_venues(self):
        resp = self._make_get_call('/venue-activity-scan')
        return resp

    def send_slack_message(self, payload):
        SimpleRequests.post(SLACK_URL, payload)

    def test_push(self):
        data = {
            "text": "test push, function is working",
            "icon_emoji": ":robot_face:",
            "username": "HealthBot❤️",
            "channel": "#sensor-network"
        }
        self.send_slack_message(data)

def lambda_handler(event, context):
    client = ApiClient(API_URL)
    resp = client.get_notify_venues()
    for venue in resp['notify_venues']:
        data = {
            "text": venue['data']['message'],
            "icon_emoji": ":heart:",
            "username": "HealthBot❤️",
            "channel": "#sensor-network"
        }
        client.send_slack_message(data)

lambda_handler(None, None)
