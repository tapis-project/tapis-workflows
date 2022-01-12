from django.urls import path
from backend.views.Builds import Builds
from backend.views.BuildContexts import BuildContexts
from backend.views.Events import Events


urlpatterns = [
    path("builds/", Builds.as_view()),
    path("build-contexts/", BuildContexts.as_view()),
    path("events/", Events.as_view()),
]