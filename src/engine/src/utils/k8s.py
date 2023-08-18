import os, re

from uuid import uuid4

from core.tasks.Flavor import Flavor
from conf.constants import IS_LOCAL


from kubernetes.client import V1ResourceRequirements, V1EnvVar


def flavor_to_k8s_resource_reqs(flavor: Flavor):
    if IS_LOCAL: return None

    return V1ResourceRequirements(
        limits=flavor_to_limits(flavor)
    )

def flavor_to_limits(flavor: Flavor):
    if flavor == None: return {}

    gpu_specs = {}
    if flavor.gpu_type != None and flavor.gpu > 0:
        gpu_specs = {f"{flavor.gpu_type}": flavor.gpu }
    
    return {"cpu": flavor.cpu, "memory": flavor.memory, **gpu_specs}

def input_to_k8s_env_vars(_inputs, pipeline_work_dir, env={}, params={}, prefix=""):
    k8senvvars = []
    for input_id, _input in _inputs.items():
        # Use input[input_id].value if provided
        value = _input.value

        if value != None:
            k8senvvars.append(
                V1EnvVar(
                    name=f"{prefix}{input_id}",
                    value=value
                ),
            )
            continue

        # Raise exception if both value and value_from are None
        value_from = _input.value_from
        if value_from == None and value == None:
            raise Exception(f"Invalid input value for '{input_id}'. Value cannot be null/None")
        
        k8senvvar_value_source_key = None
        k8senvvar_value_source = None
        k8senvvar_value = None
        
        if value_from.get("env", None) != None:
            k8senvvar_value_source = "env"
            key = value_from.get("env")
            k8senvvar_value = get_value_from_env(env, key)
            if k8senvvar_value == None:
                raise Exception(f"No value found for environment variable '{value_from.get('env')}'")
            k8senvvar_value_source_key = key
        elif value_from.get("params", None) != None:
            k8senvvar_value_source = "params"
            key = value_from.get("params")
            k8senvvar_value = get_value_from_params(params, key)
            k8senvvar_value_source_key = key
        elif hasattr(value_from, "task_output"):
            k8senvvar_value_source = "task_output"
            task_id = value_from.task_output.task_id
            output_id = value_from.task_output.output_id
            
            # Get the value from the output of a previous task
            previous_task_output_path = os.path.join(
                pipeline_work_dir,
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
            input_type = _input.type
            try:
                if input_type == "string":
                    k8senvvar_value = str(contents)
                elif input_type == "int":
                    k8senvvar_value = int(contents)
                elif input_type == "float":
                    k8senvvar_value = float(contents)
                elif input_type == "binary":
                    pass
                else:
                    raise Exception(f"Error: Unsupported coercion. Cannot coerce task output '{output_id}' for task '{task_id}' to type {input_type}")
            except Exception as e:
                raise Exception(f"Error: Could not coerce output '{output_id}' for task '{task_id}' to {input_type}. Details: {e.message}")

        else:
            raise Exception("Invalid 'value_from' type: Must be oneOf type [env, params, task_output]")
        
        if k8senvvar_value == None:
            source_key_error_message = ""
            if k8senvvar_value_source_key:
                source_key_error_message = f" at key '{k8senvvar_value_source_key}'"
            raise Exception(f"Value for input {input_id} not found in source {k8senvvar_value_source}{source_key_error_message}")

        k8senvvars.append(
            V1EnvVar(
                name=f"{prefix}{input_id}",
                value=k8senvvar_value
            ),
        )

    return k8senvvars

def get_value_from_env(env, key):
    value = env.get(key, None)
    if value == None: return None
    return value.value

def get_value_from_params(params, key):
    value = params.get(key, None)
    if value == None: return None
    return value.value

def get_value_from_task_output(key):
    pass

def gen_resource_name(prefix=""):
    system_prefix = "wf"
    name = str(uuid4())
    resource_name = "-".join([system_prefix, name])
    if prefix != "":
        resource_name = "-".join([system_prefix, str(prefix), name])
    
    return re.sub(r"[-]{2,}", "-", re.sub(r"[^a-zA-Z\d\-]*", "", resource_name).strip("-")).lower()[:45]
