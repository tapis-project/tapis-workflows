from django.urls import path
from backend.views.Builds import Builds
from backend.views.Events import Events
from backend.views.Deployments import Deployments


urlpatterns = [
    path("builds/", Builds.as_view()),
    path("deployments/", Deployments.as_view()),
    path("events/", Events.as_view()),
]