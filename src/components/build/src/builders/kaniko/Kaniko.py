from core.AbstractBuilder import AbstractBuilder
from conf.configs import DEPLOYMENT_TYPE
from builders.kaniko.handlers.Kubernetes import handler as kubernetes
from builders.kaniko.handlers.Docker import handler as docker
from utils.json_to_object import json_to_object


class Kaniko(AbstractBuilder):
    def build(self, request):
        build_context = json_to_object(request)

        if DEPLOYMENT_TYPE == "docker":
            docker.handle(build_context)
        elif DEPLOYMENT_TYPE == "kubernetes":
            kubernetes.handle(build_context)


builder = Kaniko()