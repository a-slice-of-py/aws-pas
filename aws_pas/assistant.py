"""
SEE: 
- https://stackoverflow.com/questions/51930111/boto3-get-available-actions-per-service/68117893#68117893
- https://stackoverflow.com/questions/65929546/aws-cli-boto3-is-it-possible-to-know-if-a-role-or-policy-has-permissions-over-a
"""

from loguru import logger
from typing import Optional
import json
from aws_pas.utils import parse_simulation_response
from aws_pas.parser import parse_managed_policies
import boto3

DEFAULT_AWS_REGION = 'eu-central-1'
ALL_OPS_KEY = 'ALL'

class ServiceOps:

    def __init__(self, boto3_session: boto3.Session, name: str):  
        for op in boto3_session.client(name).meta.service_model.operation_names:
            setattr(self, op, f'{name}:{op}')
        setattr(self, ALL_OPS_KEY, f'{name}:*')

class AWSServices:

    def __init__(self, boto3_session: boto3.Session):
        for service in boto3_session.get_available_services():
            setattr(self, service, ServiceOps(boto3_session, service))

class PolicyAssistanceSuite:

    def __init__(self, boto3_session: Optional[boto3.Session] = None, parse_documents: bool = True):
        if boto3_session is None:
            boto3_session = boto3.Session(region_name=DEFAULT_AWS_REGION)
        logger.info(f"Boto3 session profile: {boto3_session.profile_name}")
        
        self._iam = boto3_session.client('iam')
        self.services = AWSServices(boto3_session)
        self.policies = parse_managed_policies(parse_documents)

    def get_policy_document(self,
                            policy_arn: str
                            ) -> str:        
        default_version_id = self._iam.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
        policy_document = self._iam.get_policy_version(PolicyArn=policy_arn, VersionId=default_version_id)['PolicyVersion']['Document']
        return json.dumps(policy_document)    

    def simulate_custom_policy(self,
                               policy_input_list: list,
                               action_names: list,
                               output_format: str = 'json'
                              ) -> dict:
        response = self._iam.simulate_custom_policy(
            PolicyInputList=policy_input_list,
            ActionNames=action_names
        )
        suggested_policy, logs = parse_simulation_response(response, action_names, output_format)
        logger.info(f'Entity with given policies would be: {logs}')
        if output_format == 'json' and suggested_policy:
            response['suggested_policy'] = suggested_policy
        return response

    def simulate_principal_policy(self,
                                  policy_source_arn: str,
                                  action_names: list,
                                  output_format: str = 'json'
                                  ) -> dict:
        response = self._iam.simulate_principal_policy(
            PolicySourceArn=policy_source_arn,
            ActionNames=action_names
            )
        suggested_policy, logs = parse_simulation_response(response, action_names, output_format)
        logger.info(f'{policy_source_arn} is: {logs}')
        if output_format == 'json' and suggested_policy:
            response['suggested_policy'] = suggested_policy
        return response