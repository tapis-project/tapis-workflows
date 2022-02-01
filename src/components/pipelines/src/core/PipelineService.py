from core.ActionDispatcher import action_dispatcher
from core.BuildActionDispatcherResolver import resolver
from helpers.ContextResolver import context_resolver
from utils.status_to_text import status_to_text


class PipelineService:
    def start(self, pipeline_context):
        
        pipeline = pipeline_context.pipeline
        directives = pipeline_context.directives
        event = pipeline_context.event

        print(f"Pipeline '{pipeline.name}' started")

        # Get the build action. There should only be one
        build_action = self._get_actions_by_stage(pipeline.actions, "build")[0]
        
        # Set the repository from which the code containing the Dockerfile
        # will be pulled
        context = context_resolver.resolve(build_action.context)

        # Set the image registry to which the image will be pushed after build
        destination = self.resolve_destination(build_action, event, directives)

        # Returns a build dispatcher for the specified image builder and
        # deployment type
        dispatcher = resolver.resolve(build_action)

        status = dispatcher.dispatch(build_action, context, destination, directives)

        # If build succeeded, run other actions
        if status == 0:
            self.run_actions(pipeline.actions)

        print(f"Pipeline '{pipeline.name}' ended")

    def run_actions(self, actions):
        # Get post build actions
        actions = self._get_actions_by_stage(actions, "post_build")

        if len(actions) == 0:
            return
        
        for action in actions:
            print(f"Action '{action.name}' start:")
            status = action_dispatcher.dispatch(action)
            print(f"Action '{action.name}' {status_to_text(status)}")
        
    def resolve_destination(self, action, event, directives=None):

        if action.destination == None:
            return None

        # Default to latest tag
        tag = action.destination.tag
        if tag is None:
            tag = "latest"

        # The image tag can be overwritten by specifying directives in the 
        # commit message. Image tagging directives take precedence over the
        # the image_property of the pipeline.
        if directives is not None:
            for key, value in directives.__dict__.items():
                if key == "CUSTOM_TAG" and key is not None:
                    tag = value
                elif key == "CUSTOM_TAG" and key is None:
                    tag = action.destination.tag
                elif key == "COMMIT_DESTINATION":
                    tag = event.commit_sha
            
        destination = action.destination.url + f":{tag}"

        return destination

    def _get_actions_by_stage(self, actions, stage):
        return list(filter(lambda a: a.stage == stage, actions))

pipeline_service = PipelineService()