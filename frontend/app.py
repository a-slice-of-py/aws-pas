import streamlit as st
import re
import json
import boto3
from streamlit_echarts import st_echarts

st.set_page_config(
    page_title='AWS RPI',
    layout='wide',
    initial_sidebar_state='auto'
)

st.markdown('# AWS PAS')
st.caption('Policy Assistance Suite')

boto3_session = ...
iam = boto3_session.client('iam')

@st.experimental_memo
def get_roles() -> list:
    response = iam.list_roles()
    roles = response['Roles']
    while response['IsTruncated']:
        response = iam.list_roles(Marker=response['Marker'])
        roles.extend(response['Roles'])
    return roles

@st.experimental_memo
def get_policies(role_name: str) -> list:
    response = iam.list_role_policies(RoleName=role_name)
    policies = response['PolicyNames']
    while response['IsTruncated']:
        response = iam.list_role_policies(RoleName=role_name, Marker=response['Marker'])
        policies.extend(response['PolicyNames'])
    return policies

inspector, explorer = st.tabs(['Role Policy Inspector', 'Service Ops Explorer'])

with inspector:
    left, center, right = st.columns(3)

    with left:
        role_name_filter = st.text_input('Filter')

    with center:
        available_roles = get_roles()
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
        available_policies = get_policies(role_name)
        policy_name = st.selectbox(
            label='Policy',
            options=available_policies
        )

    policy = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)['PolicyDocument']['Statement']

    policy_length = sum(
        len(statement['Action']) if isinstance(statement['Action'], list) else 1
        for statement in policy
    )

    data = {
            'name': 'Statement',
            'children': [
                {
                    'name': statement['Effect'] if 'Condition' not in statement else f"{statement['Effect']}\n {json.dumps(statement['Condition'], indent=0)}",
                    'children': [
                        {
                            'name': action,
                            'children': [
                                {
                                    'name': resource
                                }
                                for resource in statement['Resource']]
                                if isinstance(statement['Resource'], list)
                                else [{'name': statement['Resource']}]
                        } for action in statement['Action']] 
                        if isinstance(statement['Action'], list) 
                        else [{'name': statement['Action'], 'children': [
                                {
                                    'name': resource
                                }
                                for resource in statement['Resource']]
                                if isinstance(statement['Resource'], list)
                                else [{'name': statement['Resource']}]}]
                }
                for statement in policy
            ]
        }
    options = {
        'tooltip': {
            'trigger': 'item',
            'triggerOn': 'mousemove'
        },
        'series': [
            {
                'type': 'tree',
                'data': [data],
                'top': '5%',
                'left': '7%',
                'bottom': '5%',
                'right': '25%',
                'symbolSize': 5,
                'edgeShape': 'polyline',
                'initialTreeDepth': 3,
                'lineStyle': {'width': 0.5},
                'label': {
                    'position': 'top',
                    'verticalAlign': 'middle',
                    'align': 'right',
                    'fontSize': 12
                },
                'leaves': {
                    'label': {
                        'position': 'right',
                        'verticalAlign': 'middle',
                        'align': 'left'
                    }
                },
                'emphasis': {
                    'focus': 'descendant',
                    'label': {'color': 'orange', 'fontWeight': 'bold'}
                },
                'expandAndCollapse': True,
                'animationDuration': 550,
                'animationDurationUpdate': 750
            }
        ]
    }
    PIXEL_PER_ACTION = 50

    __, left, center, right = st.columns(4) 
    with left:
        st.markdown('#### Effect | Condition')
    with center:
        st.markdown('#### service:Action')
    with right:
        st.markdown('#### Resource(s)')
    st_echarts(options=options, theme='light', height=f'{PIXEL_PER_ACTION*policy_length}px')

with explorer:
    st.write('I am a placeholder')

    if False:
        def get_prefix(operation_name: str):
            return re.findall('[A-Z][^A-Z]*', operation_name)[0]

        options = {
        'tooltip': {
                'show': True
            },
        'series': [
            {
            'type': 'treemap',
            'width': '98%',
            'height': '88%',
            'roam': True,
            'leafDepth': 1,
            'data': [
                {
                'name': service_name,
                'value': len(boto3_session.client(service_name=service_name).meta.service_model.operation_names),
                'children': [
                    {'name': prefix, 'value': len(list(filter(lambda x: x.startswith(prefix), boto3_session.client(service_name=service_name).meta.service_model.operation_names))), 'children': [{'name': op, 'value': 1} for op in list(filter(lambda x: x.startswith(prefix), boto3_session.client(service_name=service_name).meta.service_model.operation_names))]} 
                    for prefix in set(map(get_prefix, boto3_session.client(service_name=service_name).meta.service_model.operation_names))
                    ]
                }
                for service_name in sorted(boto3_session.get_available_services())[::-1]
            ]
            }
        ],
        'toolbox': {
                'show': True,
                'orient': 'horizontal',
                'left': 'center',
                'top': 'top',
                'feature': {
                    'restore': {
                        'title': 'Reset'
                    }
                },
            }
        }

        st_echarts(options=options, theme='light', height='1000px')
