from django.db import IntegrityError
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import Conflict, BadRequest, UnprocessableEntity, ServerError
from backend.views.http.responses.models import ModelResponse
from backend.models import Pipeline, Group
from backend.services.PipelineService import pipeline_service
from utils.attrs import has_all_keys


class Pipelines(RestrictedAPIView):
    def post(self, request):
        # Validate the request body
        prepared_request = self.prepare_request_body(
            request.body,
            [
                "id",
                "group_id",
                "context",
                "destination"
            ]
        )

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        pipeline_request = prepared_request.body

        # Set the issuer of the request as the owner
        pipeline_request["owner"] = request.username

        # Set the auto_build property to false if not in request
        if "auto_build" not in pipeline_request:
            pipeline_request["auto_build"] = False

        if "builder" not in pipeline_request:
            pipeline_request["builder"] = "kaniko"

        # Check that id of the pipeline is unique
        if Pipeline.objects.filter(id=pipeline_request["id"]).exists():
            return Conflict(f"A Pipeline already exists with the id '{pipeline_request['id']}'")

        # Check that the group_id passed by the user is a valid group
        if not Group.objects.filter(id=pipeline_request["group_id"]).exists():
            return UnprocessableEntity(f"Group '{pipeline_request['group_id']}' does not exist'")

        # Check that the user belongs to this group


        # Validate the context
        context = pipeline_request["context"]
        context_props = ["branch", "dockerfile_path", "type", "url", "visibility"]
        if not has_all_keys(context, context_props):
            return BadRequest(f"'context' in Pipline reuqest missing properties - Required props: {context_props}")
        
        # Validate credential in context
        context_cred = None if "credential" not in context else context["credential"]
        if context_cred is not None and "token" not in context_cred:
            return BadRequest(f"'credential' in 'context' missing 'token' property")

        # Validate the destination
        destination = pipeline_request["destination"]
        destination_props = ["tag", "type", "url"]
        if not has_all_keys(destination, destination_props):
            return BadRequest(f"'destination' in Pipline reuqest missing properties - Required props: {destination_props}")
        
        # Validate credential in destination
        destination_cred_props = ["username", "token"]
        if (
            "credential" not in destination
            or not has_all_keys(destination["credential"], destination_cred_props)
        ):
            return BadRequest(f"'credential' in 'destination' missing properties - Required props: {destination_cred_props}")
        
        pipeline = None
        try:
            pipeline = Pipeline.objects.create(
                auto_build=pipeline_request["auto_build"],
                group_id=pipeline_request["group_id"],
                branch=pipeline_request["context"]["branch"],
                builder=pipeline_request["builder"],
                context_type=pipeline_request["context"]["type"],
                destination_type=pipeline_request["destination"]["type"],
                dockerfile_path=pipeline_request["context"]["dockerfile_path"],
                image_tag=pipeline_request["destination"]["tag"],
                owner=pipeline_request["owner"]
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        return ModelResponse(result=pipeline)

        # # Create the context for the build action of this pipeline
        # pipeline_service.validate(pipeline_request)

        # # Return bad request response if context could not be validated
        # if pipeline_service.error is not None:
        #     return BadRequest(message=pipeline_service.error)

        # try:
        #     pipeline = pipeline_service.build(pipeline_request)
        # except Exception as e:
        #     return ServerError(f"Error creating Pipline '{pipeline_request['id']}': {str(e)}")

        # return ModelResponse(pipeline)
