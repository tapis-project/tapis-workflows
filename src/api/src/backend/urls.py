from django.urls import path
from django.conf import settings

from backend.views.Tasks import Tasks
from backend.views.Auth import Auth
from backend.views.RunPipeline import RunPipeline
from backend.views.Groups import Groups
from backend.views.HealthCheck import HealthCheck
from backend.views.Identities import Identities
from backend.views.Pipelines import Pipelines
from backend.views.Users import Users
from backend.views.Nuke import Nuke
from backend.views.ChangePipelineOwner import ChangePipelineOwner
from backend.views.Archives import Archives
from backend.views.AddPipelineArchive import AddPipelineArchive
from backend.views.RemovePipelineArchive import RemovePipelineArchive
from backend.views.ListPipelineArchives import ListPipelineArchives
from backend.views.PipelineRuns import PipelineRuns
from backend.views.TaskExecutions import TaskExecutions
from backend.views.UpdatePipelineRunStatus import UpdatePipelineRunStatus
from backend.views.UpdateTaskExecutionStatus import UpdateTaskExecutionStatus
from backend.views.CreateTaskExecution import CreateTaskExecution
from backend.views.ETLPipelines import ETLPipelines


urlpatterns = [
    path("healthcheck", HealthCheck.as_view(), name="healthcheck"),

    # Auth
    path("auth", Auth.as_view(), name="auth"),

    # Identities
    path("identities", Identities.as_view(), name="identities"),
    path("identities/<str:identity_uuid>", Identities.as_view(), name="identity"),
    
    # Groups
    path("groups", Groups.as_view(), name="groups"),
    path("groups/<str:group_id>", Groups.as_view(), name="group"),

    # Group Users
    path("groups/<str:group_id>/users", Users.as_view(), name="users"),
    path("groups/<str:group_id>/users/<str:username>", Users.as_view(), name="user"),

    # Archives
    path("groups/<str:group_id>/archives", Archives.as_view(), name="archives"),
    path("groups/<str:group_id>/archives/<str:archive_id>", Archives.as_view(), name="archive"),

    # Pipelines
    path("groups/<str:group_id>/ci", Pipelines.as_view(), name="ci"),
    path("groups/<str:group_id>/pipelines", Pipelines.as_view(), name="pipelines"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>", Pipelines.as_view(), name="pipeline"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/owner/<str:username>", ChangePipelineOwner.as_view(), name="changePipelineOwner"),

    # Tasks
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/tasks", Tasks.as_view(), name="tasks"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/tasks/<str:task_id>", Tasks.as_view(), name="task"),

    # Pipeline Archives
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/archives", ListPipelineArchives.as_view(), name="listPipelineArchives"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/archives/add", AddPipelineArchive.as_view(), name="addPipelineArchive"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/archives/remove", RemovePipelineArchive.as_view(), name="removePipelineArchive"),
    
    # Trigger pipelines
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/run", RunPipeline.as_view(), name="runPipeline"),

    # Pipeline Runs
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/runs", PipelineRuns.as_view(), name="pipelineRuns"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/runs/<str:pipeline_run_uuid>", PipelineRuns.as_view(), name="pipelineRun"),
    
    # NOTE The route below must come before the route below it as it matches
    # the more general pattern layed out in the latter route
    # Task Executions
    path("executor/runs/<str:pipeline_run_uuid>/executions", CreateTaskExecution.as_view(), name="createTaskExecution"),
    
    # Pipeline Runs cont.
    path("executor/runs/<str:pipeline_run_uuid>/<str:status>", UpdatePipelineRunStatus.as_view(), name="updatePipelineRunStatus"),

    # Task Executions
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/runs/<str:pipeline_run_uuid>/executions", TaskExecutions.as_view(), name="taskExecutions"),
    path("groups/<str:group_id>/pipelines/<str:pipeline_id>/runs/<str:pipeline_run_uuid>/executions/<str:task_execution_uuid>", TaskExecutions.as_view(), name="taskExecution"),
    path("executor/executions/<str:task_execution_uuid>/<str:status>", UpdateTaskExecutionStatus.as_view(), name="updateTaskExecutionStatus"),

    # Beta features
    path("beta/groups/<str:group_id>/etl", ETLPipelines.as_view(), name="etl"),
]

# NOTE This is handy, but there is the distinct posibility that someone malicious
# could add the production env to the list and hit the endpoint and nuke the prod db.
# TODO Reconsider this endpoint
if settings.ENV in ["LOCAL", "DEV", "STAGE"]:
    urlpatterns.append(path("nuke", Nuke.as_view(), name="nuke"))