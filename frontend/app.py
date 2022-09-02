import streamlit as st
import boto3
from frontend.visual import plot_policy

ROLE_PLACEHOLDER = 'ROLE_NAME'

st.set_page_config(
    page_title='AWS PAS',
    layout='wide',
    initial_sidebar_state='auto'
)
st.title('# Policy Assistance Suite')

# 1. Choose AWS PROFILE
profile_name = ...

def set_boto_session(profile_name: str) -> tuple:
    boto3_session = boto3.Session(
        region_name='eu-central-1', 
        profile_name=profile_name
        )
    iam = boto3_session.client('iam')
    return boto3_session, iam

__, iam = set_boto_session(profile_name)

# 2. Cached functions
@st.experimental_memo
def get_roles(profile_name: str) -> list:
    __, iam = set_boto_session(profile_name)
    response = iam.list_roles()
    roles = response['Roles']
    while response['IsTruncated']:
        response = iam.list_roles(Marker=response['Marker'])
        roles.extend(response['Roles'])
    return roles


@st.experimental_memo
def get_policies(profile_name: str, role_name: str) -> list:
    __, iam = set_boto_session(profile_name)
    # Inline policies
    response = iam.list_role_policies(RoleName=role_name)
    policies = response['PolicyNames']
    while response['IsTruncated']:
        response = iam.list_role_policies(
            RoleName=role_name, Marker=response['Marker'])
        policies.extend(response['PolicyNames'])
    # Managed policies
    response = iam.list_attached_role_policies(RoleName=role_name)
    policies.extend(list(map(lambda x: x['PolicyArn'], response['AttachedPolicies'])))
    while response['IsTruncated']:
        response = iam.list_attached_role_policies(
            RoleName=role_name, Marker=response['Marker'])
        policies.extend(list(map(lambda x: x['PolicyArn'], response['AttachedPolicies'])))
    return policies


def get_services(boto3_session) -> list:
    return sorted(boto3_session.get_available_services())[::-1]


@st.experimental_memo
def get_available_operations(profile_name: str) -> dict:
    boto3_session, __ = set_boto_session(profile_name)
    _available_services = get_services(boto3_session)
    available_services = {}
    for service_name in _available_services:
        available_services[service_name] = boto3_session.client(
            service_name=service_name).meta.service_model.operation_names
    return available_services

# 3. Tabs container
inspector, generator = st.tabs(
    ['Role Policy Inspector', 'CDK Policy Generator'])

with inspector:
    left, center, right = st.columns(3)

    with left:
        role_name_filter = st.text_input('Filter')

    with center:
        available_roles = get_roles(profile_name)
        _available_roles = (
            available_roles if not role_name_filter
            else list(filter(lambda x: role_name_filter in x['RoleName'], available_roles))
        )
        selected_role = st.selectbox(
            label='Role',
            options=_available_roles,
            format_func=lambda x: x['RoleName']
        )

    with right:
        role_name = selected_role['RoleName']
        available_policies = get_policies(profile_name, role_name)

    if available_policies:
        with right:
            policy_id = st.selectbox(
                label='Policy',
                options=available_policies
            )
    else:
        st.error('No policies available.', icon='❌')
        st.stop()

    __, left, center, right = st.columns(4)
    with left:
        st.markdown('#### Effect | Condition')
    with center:
        st.markdown('#### service:Action')
    with right:
        st.markdown('#### Resource(s)')
    
    if policy_id.startswith('arn:aws:iam::aws:policy'):
        version_id = iam.get_policy(PolicyArn=policy_id)['Policy']['DefaultVersionId']
        policy = iam.get_policy_version(PolicyArn=policy_id, VersionId=version_id)['PolicyVersion']['Document']['Statement']
    else:
        policy = iam.get_role_policy(RoleName=role_name, PolicyName=policy_id)[
            'PolicyDocument']['Statement']
    plot_policy(policy)

with generator:

    service2ops = get_available_operations(profile_name)

    available_operations = sorted(
        f'{service_name}:{op}'
        for service_name, available_ops in service2ops.items()
        for op in available_ops
    )

    actions_to_add = st.multiselect(
        label='Actions',
        options=available_operations
    )

    suggested_policy = f"""
    ```python
    {ROLE_PLACEHOLDER}.add_to_principal_policy(
        aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions={actions_to_add},
            resources=[
                '*'
            ]
        )
    )
    ```
    """
    st.markdown(suggested_policy)
