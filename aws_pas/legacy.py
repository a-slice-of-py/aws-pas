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
            'value': len(available_ops),
            'children': [
                {
                    'name': prefix, 
                    'value': len(list(filter(lambda x: x.startswith(prefix), available_ops))), 
                    'children': [
                        {'name': op, 'value': 1} 
                        for op in list(filter(lambda x: x.startswith(prefix), available_ops))]
                } 
                for prefix in set(map(get_prefix, available_ops))
                ]
            }
            for service_name, available_ops in service2ops.items()
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
