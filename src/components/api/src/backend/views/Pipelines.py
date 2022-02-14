from django.db import IntegrityError
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import Conflict, BadRequest, UnprocessableEntity, Forbidden, ServerError
from backend.views.http.responses.models import ModelResponse
from backend.views.http.requests import PipelineCreateRequest
from backend.models import Pipeline, Group
from backend.services.PipelineService import pipeline_service
from utils.attrs import has_all_keys


class Pipelines(RestrictedAPIView):
    def post(self, request):
        # Validate the request body
        prepared_request = self.prepare(PipelineCreateRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Set the issuer of the request as the owner
        body["owner"] = request.username

        # Check that id of the pipeline is unique
        if Pipeline.objects.filter(id=body["id"]).exists():
            return Conflict(f"A Pipeline already exists with the id '{body['id']}'")

        # Check that the group_id passed by the user is a valid group
        if not Group.objects.filter(id=body["group_id"]).exists():
            return UnprocessableEntity(f"Group '{body['group_id']}' does not exist'")

        # Check that the user belongs to or owns this group
        group = Group.object.filter(id=body["group_id"])
        group_users = group.users.all()
        if (
            request.username != group.owner
            and request.username not in list(filter(lambda u: u.username == request.username, group_users))
        ):
            return Forbidden("You cannot create a pipeline for this group")

        try:
            pipeline = Pipeline.objects.create(
                auto_build=body["auto_build"],
                group_id=body["group_id"],
                branch=body["context"]["branch"],
                builder=body["builder"],
                context_type=body["context"]["type"],
                destination_type=body["destination"]["type"],
                dockerfile_path=body["context"]["dockerfile_path"],
                image_tag=body["destination"]["tag"],
                owner=body["owner"]
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        return ModelResponse(result=pipeline)
