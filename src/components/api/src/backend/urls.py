from django.urls import path
from backend.views.Actions import Actions
from backend.views.Auth import Auth
from backend.views.Builds import Builds
from backend.views.Contexts import Contexts
from backend.views.Credentials import Credentials
from backend.views.Destinations import Destinations as Destinations
from backend.views.Events import Events
from backend.views.Aliases import Aliases
from backend.views.Groups import Groups
from backend.views.GroupUsers import GroupUsers
from backend.views.Pipelines import Pipelines
from backend.views.Policies import Policies


urlpatterns = [
    path("actions/", Actions.as_view()),
    path("aliases/", Aliases.as_view()),
    path("auth/", Auth.as_view()),
    path("builds/", Builds.as_view()),
    path("contexts/", Contexts.as_view()),
    path("credentials/", Credentials.as_view()),
    path("destination/", Destinations.as_view()),
    path("events/", Events.as_view()),
    path("groups/", Groups.as_view()),
    path("groups/", GroupUsers.as_view()),
    path("pipelines/", Pipelines.as_view()),
    path("policies/", Policies.as_view()),
]