from django.contrib import admin

from backend.models import Action, Identity, Build, Credentials, Context, Destination, Group, GroupUser, Event, Pipeline

models = [
    Action,
    Identity,
    Build,
    Credentials,
    Context,
    Destination,
    Group,
    GroupUser,
    Event,
    Pipeline,
]

# Register your models here.
for model in models:
    admin.site.register(model)