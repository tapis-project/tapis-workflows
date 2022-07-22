from django.urls import path
from django.conf import settings

from backend.views.Tasks import Tasks
from backend.views.Auth import Auth
from backend.views.RunPipelineWebhook import RunPipelineWebhook
from backend.views.Events import Events
from backend.views.Groups import Groups
from backend.views.HealthCheck import HealthCheck
from backend.views.Identities import Identities
from backend.views.Pipelines import Pipelines
from backend.views.Users import Users
from backend.views.Nuke import Nuke
from backend.views.ChangePipelineOwner import ChangePipelineOwner
from backend.views.Archives import Archives
from backend.views.AddPipelineArchive import AddPipelineArchive
from backend.views.RemovePipelineArchive import RemovePipelineArchive
from backend.views.ListPipelineArchives import ListPipelineArchives


urlpatterns = [
    path("healthcheck", HealthCheck.as_view()),

    # Auth
    path("auth", Auth.as_view()),

    # Identities
    path("identities", Identities.as_view()),
    path("identities/<str:identity_uuid>", Identities.as_view()),
    
    # Groups
    path("groups", Groups.as_view()),
    path("groups/<str:group_id>", Groups.as_view()),

    # Group Users
    path("groups/<str:group_id>/users", Users.as_view()),
    path("groups/<str:group_id>/users/<str:username>", Users.as_view()),

    # Archives
    path("groups/<str:group_id>/archives", Archives.as_view()),
    path("groups/<str:group_id>/archives/<str:archive_id>", Archives.as_view()),

    # Pipelines
    path("groups/<str:group_id>/ci", Pipelines.as_view()),
    path("groups/<str:group_id>/pipelines", Pipelines.as_view()),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>", Pipelines.as_view()),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/owner/<str:username>", ChangePipelineOwner.as_view()),

    # Tasks
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/tasks", Tasks.as_view()),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/tasks/<str:task_id>", Tasks.as_view()),

    # Pipeline Archives
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/archives", ListPipelineArchives.as_view()),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/archives/add", AddPipelineArchive.as_view()),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/archives/remove", RemovePipelineArchive.as_view()),
    
    # Trigger pipelines
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/webhook", RunPipelineWebhook.as_view()),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/events", Events.as_view()),

    # Events
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/events/<str:event_uuid>", Events.as_view()),
]

# NOTE This is handy, but there is the distinct posibility that someone malicious
# could add the production env to the list and hit the endpoint and nuke the prod db.
# TODO Reconsider this endpoint
if settings.ENV in ["LOCAL", "DEV", "STAGE"]:
    urlpatterns.append(path("nuke", Nuke.as_view()))