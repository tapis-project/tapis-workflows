from helpers.ContextResolver import context_resolver


class BaseBuildDispatcher:
    def _resolve_context_string(self, action):
        # Resolve the repository from which the code containing the Dockerfile
        # will be pulled
        return context_resolver.resolve(action.context)

    def _resolve_destination_string(self, action, event, directives=None):

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