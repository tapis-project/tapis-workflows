from django.urls import path
from backend.views.Actions import Actions
from backend.views.Auth import Auth
from backend.views.WebhookEvents import WebhookEvents
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
    path("healthcheck/", HealthCheck.as_view()),

    # Auth
    path("auth/", Auth.as_view()),

    # Identities
    path("identities/", Identities.as_view()),
    path("identities/<str:identity_uuid>", Identities.as_view()),
    
    # Groups
    path("groups/", Groups.as_view()),
    path("groups/<str:id>", Groups.as_view()),
    path("groups/<str:group_id>/users/", Users.as_view()),
    path("groups/<str:group_id>/users/<str:username>", Users.as_view()),

    # Archives
    path("archives/<str:group_id>", Archives.as_view()),
    path("archives/<str:group_id>/<str:archive_id>", Archives.as_view()),

    # Pipelines
    path("pipelines/", Pipelines.as_view()),
    path("ci/", Pipelines.as_view()),
    path("pipelines/<str:group_id>/<str:pipeline_id>/actions/", Actions.as_view()),
    path("pipelines/<str:group_id>/<str:pipeline_id>/actions/<str:action_id>", Actions.as_view()),
    path("pipelines/<str:group_id>/<str:id>", Pipelines.as_view()),
    path("pipelines/<str:group_id>/<str:pipeline_id>/changeOwner/<str:username>", ChangePipelineOwner.as_view()),

    # Pipeline Archives
    path("pipelines/<str:group_id>/<str:pipeline_id>/archives/", ListPipelineArchives.as_view()),
    path("pipelines/<str:group_id>/<str:pipeline_id>/archives/add", AddPipelineArchive.as_view()),
    path("pipelines/<str:group_id>/<str:pipeline_id>/archives/remove", RemovePipelineArchive.as_view()),
    
    # Trigger pipelines
    path("webhooks/pipelines/<str:group_id>/<str:pipeline_id>", WebhookEvents.as_view()),
    path("pipelines/<str:pipeline_id>/events/", Events.as_view()),

    # Events
    path("pipelines/<str:pipeline_id>/events/<str:event_uuid>", Events.as_view()),
    path("nuke/", Nuke.as_view()), # TODO Remove
]