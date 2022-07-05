from textwrap import dedent
import json

def parse_simulation_response(response: dict, 
                              action_names: list,
                              output_format: str
                              ) -> tuple:
    assert not response['IsTruncated'], "Response has been truncated: more items to be retrieved."
    logs, actions_to_add = [], []
    for action in action_names:
        result = (
            list(
                filter(
                    lambda x: x['EvalActionName'] == action,
                    response['EvaluationResults']
                )
            )
            .pop()                
        )
        if result['EvalDecision'] == 'allowed':
            logs.append(f"    ✅     allowed to perform {action} thanks to {', '.join(map(lambda x: x['SourcePolicyId'], result['MatchedStatements']))}.")
        else:
            logs.append(f"    ⛔ not allowed to perform {action} [{result['EvalDecision']}].")
            actions_to_add.append(action)
    suggested_policy = None
    if actions_to_add:
        if output_format == 'json':
            suggested_policy = json.dumps({
                "Version": "2012-10-17", 
                "Statement": [
                    {
                        "Effect": "Allow", 
                        "Action": actions_to_add, 
                        "Resource": "*"
                    }
                ]
            })
        elif output_format == 'cdk':
            placeholder_role = 'PUT_HERE_YOUR_ROLE'
            suggested_policy = f"""
            ```
            {placeholder_role}.add_to_principal_policy(
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
        logs.append(f"Suggested policy addition: {dedent(suggested_policy)}")
    logs = '\n' + '\n'.join(logs)
    return suggested_policy, logs