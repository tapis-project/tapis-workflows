from django.urls import path
from backend.views.Builds import Builds
from backend.views.Configs import Configs
from backend.views.Events import Events


urlpatterns = [
    path("builds/", Builds.as_view()),
    path("configs/", Configs.as_view()),
    path("events/", Events.as_view()),
]