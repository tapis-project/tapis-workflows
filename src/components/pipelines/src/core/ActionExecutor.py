import os, uuid

from kubernetes import config, client

from core.resources import Resource

class ActionExecutor:
    _resources: list[Resource] = []

    def __init__(self, action, message):
        self.action = action
        self.pipeline = message.pipeline
        self.group = message.group
        self.event = message.event
        self.directives = message.directives
        self.message = message

        # Create the base directory for all files and output created during this action execution
        work_dir = f"{self.message.pipeline.work_dir}{action.id}/"
        os.mkdir(work_dir)

        # Create the scratch dir for files created in support of the action execution
        scratch_dir = f"{work_dir}scratch/"
        os.mkdir(scratch_dir)
        self.action.scratch_dir = scratch_dir

        # Create the output dir in which the output of the action execution will be stored
        output_dir = f"{work_dir}output/"
        os.mkdir(output_dir)
        self.action.output_dir = output_dir

    def _register_resource(self, resource: Resource):
        self._resources.append(resource)

    def _cleanup(self, resources: list[Resource]=[]):
        # If no resources passed, cleanup all resources
        if len(resources) == 0:
            resources = self._resources

        for resource in resources:
            pass