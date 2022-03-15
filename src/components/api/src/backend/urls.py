from django.urls import path
from backend.views.Actions import Actions
from backend.views.Auth import Auth
from backend.views.Builds import Builds
from backend.views.Contexts import Contexts
from backend.views.Credentials import Credentials
from backend.views.Destinations import Destinations
from backend.views.WebhookEvents import WebhookEvents
from backend.views.APIEvents import APIEvents
from backend.views.Groups import Groups
from backend.views.Identities import Identities
from backend.views.Pipelines import Pipelines
from backend.views.Policies import Policies
from backend.views.Nuke import Nuke


urlpatterns = [
    path("actions/", Actions.as_view()),
    path("actions/<str:pipeline_id>", Actions.as_view()),
    path("auth/", Auth.as_view()),
    path("builds/", Builds.as_view()),
    path("contexts/", Contexts.as_view()),
    path("credentials/", Credentials.as_view()),
    path("destination/", Destinations.as_view()),
    path("webhooks/pipelines/<str:pipeline_id>", WebhookEvents.as_view()),
    path("events/<str:pipeline_id>", APIEvents.as_view()),
    path("groups/", Groups.as_view()),
    path("groups/<str:id>", Groups.as_view()),
    path("identities/", Identities.as_view()),
    path("pipelines/", Pipelines.as_view()),
    path("pipelines/<str:id>", Pipelines.as_view()),
    path("policies/", Policies.as_view()),
    path("nuke/", Nuke.as_view()), # TODO Remove
]