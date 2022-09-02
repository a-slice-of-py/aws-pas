from streamlit_echarts import st_echarts
import json

PIXEL_PER_ACTION = 50


def plot_policy(policy: list) -> None:

    policy_length = sum(
        len(statement['Action'])
        if isinstance(statement['Action'], list)
        else 1
        for statement in policy
    )

    data = {
        'name': 'Statement',
        'children': [
                {
                    'name': (
                        statement['Effect'] 
                        if 'Condition' not in statement 
                        else f"{statement['Effect']}\n {json.dumps(statement['Condition'], indent=0)}"
                    ),
                    'children': [
                        {
                            'name': action,
                            'children': (
                                [{'name': resource} for resource in statement['Resource']]
                                if isinstance(statement['Resource'], list)
                                else [{'name': statement['Resource']}]
                            )
                        } for action in statement['Action']]
                        if isinstance(statement['Action'], list)
                        else [{
                            'name': statement['Action'], 
                            'children': 
                                [{'name': resource} for resource in statement['Resource']]
                                if isinstance(statement['Resource'], list)
                                else [{'name': statement['Resource']}]}]
                }
            for statement in sorted(policy, key=lambda x: x['Action'][0] if isinstance(x['Action'], list) else x['Action'])
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
                    'fontSize': 14
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
                    'label': {'color': '#FF4B4B', 'fontWeight': 'bold'}
                },
                'expandAndCollapse': True,
                'animationDuration': 550,
                'animationDurationUpdate': 750
            }
        ]
    }

    st_echarts(options=options, theme='light',
               height=f'{PIXEL_PER_ACTION*policy_length}px')
