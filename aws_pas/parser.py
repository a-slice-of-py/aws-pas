"""
SEE: https://github.com/Netflix-Skunkworks/policyuniverse
"""

from typing import List, Union, Optional
from dataclasses import dataclass, make_dataclass
import json
from policyuniverse.policy import Policy

from aws_pas import DATA_PATH


@dataclass
class PolicyStatement:
    Action: Optional[Union[str, List[str]]] = None
    Effect: Optional[str] = None
    Resource: Optional[Union[str, List[str]]] = None
    Condition: Optional[dict] = None
    NotAction: Optional[Union[str, List[str]]] = None
    NotResource: Optional[Union[str, List[str]]] = None
    Sid: Optional[str] = None


@dataclass
class PolicyDocument:
    Statement: Union[dict, List[dict]]
    Version: str
    
    def __post_init__(self) -> None:
        if isinstance(self.Statement, list):
            self.Statement = [PolicyStatement(**s) for s in self.Statement]
        elif isinstance(self.Statement, dict):
            self.Statement = PolicyStatement(**self.Statement)

    def to_json(self) -> str:
        return json.dumps({
            'Version': self.Version,
            'Statement': list(
                map(
                    lambda x: {k: v for k, v in x.__dict__.items() if v}, 
                    self.Statement
                )
            )
        })



@dataclass
class ManagedPolicy:
    Arn: str
    AttachmentCount: str
    CreateDate: str
    DefaultVersionId: str
    Document: dict    
    IsAttachable: str
    IsDefaultVersion: str
    Path: str
    PermissionsBoundaryUsageCount: str
    PolicyId: str
    PolicyName: str
    UpdateDate: str
    VersionId: str
    _parse_document: bool

    def __post_init__(self) -> None:
        if self._parse_document:
            self.DocumentParsed = Policy(self.Document)
        self.Document = PolicyDocument(**self.Document)


def parse_managed_policies(parse_document: bool) -> object:
    with open(f'{DATA_PATH}/all_aws_managed_policies.json', 'r') as f:
        managed_policies = json.load(f)
    parsed_policies = [ManagedPolicy(**{**{'_parse_document': parse_document}, **policy}) for policy in managed_policies.values()]
    ManagedPolicies = make_dataclass(
        'AWSManagedPolicies', 
        [(p.PolicyName.replace('-', '_'), ManagedPolicy) for p in parsed_policies]
        )
    return ManagedPolicies(*parsed_policies)