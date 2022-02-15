from django.contrib import admin

from backend.models import Account, Action, Alias, Build, Credential, Context, Destination, Group, GroupUser, Event, Pipeline, Policy

models = [
    Account,
    Action,
    Alias,
    Build,
    Credential,
    Context,
    Destination,
    Group,
    GroupUser,
    Event,
    Pipeline,
    Policy
]

# Register your models here.
for model in models:
    admin.site.register(model)