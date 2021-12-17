from django.db import models


class Build(models.Model):
    STATUS_QUEUED = 0
    STATUS_FETCHING = 1
    STATUS_IN_PROGRESS = 2
    STATUS_PUSHING = 3
    STATUS_FAILED = 4
    STATUS_SUCCESS = 5
    STATUSES = [
        ( STATUS_QUEUED, "queued" ),
        ( STATUS_FETCHING, "fetching" ),
        ( STATUS_IN_PROGRESS, "in_progress" ),
        ( STATUS_PUSHING, "pushing" ),
        ( STATUS_FAILED, "failed" ),
        ( STATUS_SUCCESS, "success" ),
    ]
    image = models.CharField(max_length=128)
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=STATUS_QUEUED)
    event = models.ForeignKey("Event", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Config(models.Model):
    image_repository = models.CharField(max_length=128)

class Event(models.Model):
    EVENT_PUSH = "P"
    EVENT_MERGE_REQUEST_EVENT = "M"
    EVENT_TYPES = [
        (EVENT_PUSH, "push"),
        (EVENT_MERGE_REQUEST_EVENT, "merge_request_event"),
    ]
    branch = models.CharField(max_length=255)
    user = models.CharField(max_length=255)
    commit = models.CharField(max_length=128)
    message = models.TextField(max_length=1024, null=True)
    event_type = models.CharField(max_length=1, choices=EVENT_TYPES)
    action = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)




