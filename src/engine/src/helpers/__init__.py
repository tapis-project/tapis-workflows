from helpers.GraphValidator import GraphValidator

from owe_python_sdk.schema import Params, Args


def params_validator(params: Params, args: Args):
    required_params = [key for key in params if params[key].required]
    missing_args = []
    print("ARGS", args)
    for param in required_params:
        if getattr(args.get(param, None), "value", None) == None:
            missing_args.append(param)

    err = None
    succeeded = True
    if len(missing_args) > 0:
        err = f"Workflow submission validation error: Missing values for the following arguments - {missing_args}"
        succeeded = False

    return (succeeded, err)