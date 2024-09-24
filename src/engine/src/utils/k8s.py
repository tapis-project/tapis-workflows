import os, re

from uuid import uuid4

from tasks.Flavor import Flavor
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

def get_value_from_env(env, key):
    value = env.get(key, None)
    if value == None: return None
    return value.value

def get_value_from_args(args, key):
    value = args.get(key, None)
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
