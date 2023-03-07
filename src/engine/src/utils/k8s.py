from core.tasks.Flavor import Flavor
from conf.constants import FLAVORS, IS_LOCAL
from errors import InvalidFlavorError

from kubernetes.client import V1ResourceRequirements

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
