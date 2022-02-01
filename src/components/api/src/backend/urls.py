from django.urls import path
from backend.views.Builds import Builds
from backend.views.Events import Events
from backend.views.Pipelines import Pipelines


urlpatterns = [
    path("builds/", Builds.as_view()),
    path("pipelines/", Pipelines.as_view()),
    path("events/", Events.as_view())
]