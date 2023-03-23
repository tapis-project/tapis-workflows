import os

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

def input_to_k8s_env_vars(_inputs, ctx, prefix=""):
    k8s_env_vars = []
    for input_id, _input in _inputs.__dict__.items():
        # Handle for empty input
        if type(_input) != SimpleNamespace:
            raise Exception(f"Invalid input for input '{input_id}'")

        # Get the value, value_from, and type
        value = getattr(_input, "value", None)
        value_from = getattr(_input, "value_from", None)
        input_type = getattr(_input, "type", None)

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

        k8s_env_var_value_source = None
        k8s_env_var_value = None
        if hasattr(value_from, "env"):
            k8s_env_var_value_source = "env"
            env_var_key = value_from.env
            env_var = getattr(ctx.env, env_var_key, None)
            if env_var == None:
                raise Exception(f"Environment variable '{env_var_key}' does not exist.")
            k8s_env_var_value = getattr(env_var, "value", None)
        elif hasattr(value_from, "params"):
            k8s_env_var_value_source = "params"
            k8s_env_var_value = getattr(ctx.params, value_from.params, None)
        elif hasattr(value_from, "task_output"):
            k8s_env_var_value_source = "task_output"
            task_id = value_from.task_output.task_id
            output_id = value_from.task_output.output_id
            
            # Get the value from the output of a previous task
            previous_task_output_path = os.path.join(
                ctx.pipeline.work_dir,
                task_id,
                "output",
                output_id
            )
            
            # Check that the specified output file exists
            if not os.path.isfile(previous_task_output_path): raise Exception(f"Error: output '{output_id}' for task {task_id} not found")

            # Grab the value of the output from the file
            contents = None
            with open(previous_task_output_path, "r") as file:
                contents = file.read()

            # TODO Consider allowing None
            # Raise exception if output is None
            if contents == None: raise Exception(f"Error: Output '{output_id}' for task '{task_id}' is null")

            # Coerce the value of the contents into the value specified in the input
            try:
                if input_type == "string":
                    k8s_env_var_value = str(contents)
                elif input_type == "int":
                    k8s_env_var_value = int(contents)
                elif input_type == "float":
                    k8s_env_var_value = float(contents)
                elif input_type == "binary":
                    pass
                else:
                    raise Exception(f"Error: Unsupported coercion. Cannot coerce task output '{output_id}' for task '{task_id}' to type {input_type}")
            except Exception as e:
                raise Exception(f"Error: Could not coerce output '{output_id}' for task '{task_id}' to {input_type}. Details: {e.message}")

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
