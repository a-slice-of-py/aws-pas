"""Credits to https://gist.github.com/bernadinm/6f68bfdd015b3f3e0a17b2f00c9ea3f8."""

import json
from datetime import datetime

from loguru import logger


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")

boto3_session = ...
client = boto3_session.client('iam')

policies = {}

paginator = client.get_paginator('list_policies')
response_iterator = paginator.paginate(Scope='AWS')

logger.info('Retrieving policies...')
for response in response_iterator:
    for policy in response['Policies']:
        policies[policy['PolicyName']] = policy

logger.info('Parsing policies...')
for policy_name in policies:
    response = client.get_policy_version(
        PolicyArn=policies[policy_name]['Arn'],
        VersionId=policies[policy_name]['DefaultVersionId'])
    for key in response['PolicyVersion']:
        policies[policy_name][key] = response['PolicyVersion'][key]

with open('./all_aws_managed_policies.json', 'w') as f:
    json.dump(
        policies,
        f,
        sort_keys=True,
        indent=4,
        separators=(',', ': '),
        default=json_serial
    )
logger.success('Policies successfully saved.')
