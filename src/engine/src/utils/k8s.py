from core.tasks.Flavor import Flavor
from conf.constants import FLAVORS, IS_LOCAL
from errors import InvalidFlavorError
from types import SimpleNamespace

from kubernetes.client import V1ResourceRequirements, V1EnvVar

def get_k8s_resource_reqs(flavor: Flavor):
    if flavor not in FLAVORS:
        raise InvalidFlavorError(f"{flavor} is an invalid flavor")

    if IS_LOCAL: return None

    return V1ResourceRequirements(
        limits=flavor_to_limits(flavor)
    )

def flavor_to_limits(flavor: Flavor):
    if flavor not in FLAVORS:
        raise InvalidFlavorError(f"{flavor} is an invalid flavor")
    return {"cpu": flavor.cpu, "memory": flavor.memory}

def input_to_k8s_env_vars(_inputs, env, params, prefix=""):
    k8s_env_vars = []
    for input_id, _input in _inputs.__dict__.items():
        # Handle for empty input
        if type(_input) != SimpleNamespace:
            raise Exception(f"Invalid input for input '{input_id}'")

        # Get the values or value from
        value = getattr(_input, "value", None)
        value_from = getattr(_input, "value_from", None)

        # Raise exception if both value and value_from are None
        if value_from == None and value == None:
            raise Exception(f"Invalid input value for '{input_id}'. Value cannot be null/None")

        if value != None:
            k8s_env_vars.append(
                V1EnvVar(
                    name=f"{prefix}{input_id}",
                    value=value
                ),
            )
            continue

        k8s_env_var_value = None
        k8s_env_var_value_source = None
        if hasattr(value_from, "env"):
            k8s_env_var_value = getattr(env, value_from.env, None)
            k8s_env_var_value_source = "env"
        elif hasattr(value_from, "params"):
            k8s_env_var_value = getattr(params, value_from.params, None)
            k8s_env_var_value_source = "params"
        elif hasattr(value_from, "task_output"):
            # k8s_env_var_value_source = "task_output"
            raise Exception("Error: Unsupported: task_output' for 'value_from' is not yet supported")
        else:
            raise Exception("Invalid 'value_from' type: Must be oneOf type [env, params, task_output]")
        
        if k8s_env_var_value == None:
            raise Exception(f"Value for key {input_id} not found in source {k8s_env_var_value_source}")
        k8s_env_vars.append(
            V1EnvVar(
                name=f"{prefix}{input_id}",
                value=k8s_env_var_value
            ),
        )

    return k8s_env_vars
