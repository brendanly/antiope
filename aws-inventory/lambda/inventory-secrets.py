
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

import json
import os
import time
import datetime
from dateutil import tz

from lib.account import *
from lib.common import *

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)

RESOURCE_PATH = "secretsmanager"

def lambda_handler(event, context):
    logger.debug("Received event: " + json.dumps(event, sort_keys=True))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Received message: " + json.dumps(message, sort_keys=True))

    try:
        target_account = AWSAccount(message['account_id'])
        for r in target_account.get_regions():
            discover_secrets(target_account, r)

    except AssumeRoleError as e:
        logger.error("Unable to assume role into account {}({})".format(target_account.account_name, target_account.account_id))
        return()
    except ClientError as e:
        logger.error("AWS Error getting info for {}: {}".format(target_account.account_name, e))
        return()
    except Exception as e:
        logger.error("{}\nMessage: {}\nContext: {}".format(e, message, vars(context)))
        raise

def discover_secrets(target_account, region):
    '''Iterate across all regions to discover Cloudsecrets'''

    try:
        secrets = []
        client = target_account.get_client('secretsmanager', region=region)
        response = client.list_secrets()
        while 'NextToken' in response:  # Gotta Catch 'em all!
            secrets += response['SecretList']
            response = client.list_secrets(NextToken=response['NextToken'])
        secrets += response['SecretList']

        for s in secrets:
            process_secret(client, s, target_account, region)

    except EndpointConnectionError as e:
        logger.info("Region {} not supported".format(region))

def process_secret(client, secret, target_account, region):

    resource_item = {}
    resource_item['awsAccountId']                   = target_account.account_id
    resource_item['awsAccountName']                 = target_account.account_name
    resource_item['resourceType']                   = "AWS::SecretsManager::Secret"
    resource_item['source']                         = "Antiope"
    resource_item['awsRegion']                      = region
    resource_item['configurationItemCaptureTime']   = str(datetime.datetime.now())
    resource_item['configuration']                  = secret
    resource_item['supplementaryConfiguration']     = {}
    resource_item['resourceId']                     = "{}-{}-{}".format(target_account.account_id, region, secret['Name'].replace("/", "-"))
    resource_item['resourceName']                   = secret['Name']
    resource_item['errors']                         = {}
    resource_item['ARN']                            = secret['ARN']

    response = client.get_resource_policy(SecretId=secret['ARN'])
    if 'ResourcePolicy' in response:
        resource_item['supplementaryConfiguration']['ResourcePolicy']    = json.loads(response['ResourcePolicy'])
    if 'Tags' in secret:
        resource_item['tags']              = parse_tags(secret['Tags'])

    save_resource_to_s3(RESOURCE_PATH, resource_item['resourceId'], resource_item)


