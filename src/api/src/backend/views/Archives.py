from tapipy.errors import InvalidInputError

from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse
from backend.views.http.responses.errors import Conflict, Forbidden, NotFound, BadRequest, ServerError
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.requests import SystemArchive, S3Archive, IRODSArchive
from backend.models import (
    Archive, 
    ARCHIVE_TYPE_SYSTEM, 
    ARCHIVE_TYPE_S3, 
    ARCHIVE_TYPE_IRODS
)
from backend.services.GroupService import service as group_service


ARCHIVE_REQUEST_MAPPING = {
    ARCHIVE_TYPE_SYSTEM: SystemArchive,
    ARCHIVE_TYPE_S3: S3Archive,
    ARCHIVE_TYPE_IRODS: IRODSArchive
}

ARCHIVE_TYPES = [ARCHIVE_TYPE_SYSTEM, ARCHIVE_TYPE_S3, ARCHIVE_TYPE_IRODS]

class Archives(RestrictedAPIView):
    def get(self, request, group_id, archive_id=None):
        # Check that the user belongs to the group that owns this archive
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You do not have access to this archive")
        
        # Get the a list of all the archives that belong to this group
        if archive_id == None:
            return self.list(group_id)

        archive = Archive.objects.filter(
            group_id=group_id,
            id=archive_id
        ).first()

        if archive == None:
            return NotFound(message=f"Archive with id '{archive_id}' not found")

        return ModelResponse(archive)


    def list(self, group_id):
        archives = Archive.objects.filter(group_id=group_id)
        return ModelListResponse(archives)

    def post(self, request, group_id, **_):
        # Check that the user belongs to the group that owns this archive
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You do not have access to this archive")

        # Ensure the request body has a 'type' property and it is a valid value
        # before validating the rest of the request body
        if (
            "type" not in self.request_body
            or self.request_body["type"] not in ARCHIVE_REQUEST_MAPPING.keys()
        ):
            return BadRequest(f"Request body must inlcude a 'type' property with one of the following values: {ARCHIVE_TYPES}")

        # Validate the request body based on the type of pipeline specified
        prepared_request = self.prepare(ARCHIVE_REQUEST_MAPPING[self.request_body["type"]])

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Check that id of the pipeline is unique
        if Archive.objects.filter(id=body.id, group_id=group_id).exists():
            return Conflict(f"An archive already exists with the id '{body.id}'")

        # Build the archive based on the specified type and return the response
        try:
            response = getattr(self, body.type)(request, body, group_id)
        except NotImplementedError as e:
            return BadRequest(message=e)

        return response
        
    def put(self, request, group_id, archive_id):
        pass

    def patch(self, request, group_id, archive_id):
        pass

    def delete(self, request, group_id, archive_id):
        # Check that the user belongs to the group that owns this archive
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You do not have access to this archive")
        
        # Get the archive by the id provided in the path params
        archive = Archive.objects.filter(
            group_id=group_id, id=archive_id).first()

        if archive is None:
            return NotFound(f"Archive not found with id '{archive_id}'")

        archive.delete()

        return BaseResponse(message=f"Archive deleted")

    def system(self, request, body, group_id):
        client = self.api_gateway.get_client()

        try:
            res = client.systems.getUserPerms(
                systemId=body.system_id,
                userName=self.api_gateway.get_username()
            )
        except InvalidInputError as e:
            print(e)
            return BadRequest(f"System '{body.system_id}' does not exist or you do not have access to it.")
        except Exception as e:
            return ServerError(message=e)

        # Check that the requesting user had modify permissons on this system
        if "MODIFY" not in res.names:
            return Forbidden(f"You do not have 'MODIFY' permissions for system '{body.system_id}'")

        # Persist the archive to the db
        try:
            archive = Archive.objects.create(
                group_id=group_id,
                owner=request.username,
                **dict(body)
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return BadRequest(message=e)

        return ModelResponse(archive)


    def s3(self, *_):
        raise NotImplementedError(f"Archives of type '{type}' are not yet implemented")

    def irods(self, *_):
        raise NotImplementedError(f"Archives of type '{type}' are not yet implemented")

