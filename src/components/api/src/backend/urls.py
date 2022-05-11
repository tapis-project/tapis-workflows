from django.urls import path
from backend.views.Actions import Actions
from backend.views.Auth import Auth
from backend.views.Builds import Builds
from backend.views.WebhookEvents import WebhookEvents
from backend.views.Events import Events
from backend.views.Groups import Groups
from backend.views.Identities import Identities
from backend.views.Pipelines import Pipelines
from backend.views.Users import Users
from backend.views.Nuke import Nuke
from backend.views.ChangePipelineOwner import ChangePipelineOwner


urlpatterns = [
    path("auth/", Auth.as_view()),
    path("builds/", Builds.as_view()),
    path("webhooks/pipelines/<str:pipeline_id>", WebhookEvents.as_view()),
    path("groups/", Groups.as_view()),
    path("groups/<str:id>", Groups.as_view()),
    path("groups/<str:group_id>/users/", Users.as_view()),
    path("groups/<str:group_id>/users/<str:username>", Users.as_view()),
    path("identities/", Identities.as_view()),
    path("pipelines/", Pipelines.as_view()),
    path("ci/", Pipelines.as_view()),
    path("pipelines/<str:pipeline_id>/actions/", Actions.as_view()),
    path("pipelines/<str:pipeline_id>/actions/<str:action_id>", Actions.as_view()),
    path("pipelines/<str:id>", Pipelines.as_view()),
    path("pipelines/<str:pipeline_id>/events/", Events.as_view()),
    path("pipelines/<str:pipeline_id>/events/<str:event_uuid>", Events.as_view()),
    path("pipelines/<str:pipeline_id>/changeOwner/<str:username>", ChangePipelineOwner.as_view()),
    path("nuke/", Nuke.as_view()), # TODO Remove
]