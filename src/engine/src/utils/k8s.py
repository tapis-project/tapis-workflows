from core import Flavor
from conf.constants import FLAVORS
from errors import InvalidFlavorError


def flavor_to_limits(flavor: Flavor):
    if flavor not in FLAVORS:
        raise InvalidFlavorError("Flavor provided is invalid")
    return {"cpu": flavor.cpu, "memory": flavor.memory}
