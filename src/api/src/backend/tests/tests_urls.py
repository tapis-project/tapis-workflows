from django.test import SimpleTestCase
from django.urls import reverse, resolve
from backend.views import (
    AddPipelineArchive, Auth, Archives, ChangePipelineOwner, CreateTaskExecution,
    Credentials, Destinations, Events, Groups, HealthCheck, Identities,
    ListPipelineArchives, PipelineRuns, Pipelines, RemovePipelineArchive,
    TaskExecutions, Tasks, UpdatePipelineRunStatus, UpdateTaskExecutionStatus,
    Users, RunPipelineWebhook
)

from backend.conf.constants import DJANGO_TAPIS_TOKEN_HEADER
from backend.utils.fixture_loader import fixture_loader as load


VIEW_MAPPING = {
    "healthcheck": HealthCheck,
    "auth": Auth,
    "identities": Identities,
    "identity": Identities,
    "group": Groups,
    "groups": Groups,
    "user": Users,
    "users": Users,
    "archive": Archives,
    "archives": Archives,
    "ci": Pipelines,
    "pipelines": Pipelines,
    "pipeline": Pipelines,
    "changePipelineOwner": ChangePipelineOwner,
    "tasks": Tasks,
    "task": Tasks,
    "listPipelineArchives": ListPipelineArchives,
    "addPipelineArchive": AddPipelineArchive,
    "removePipelineArchive": RemovePipelineArchive,
    "runPipelineWebhook": RunPipelineWebhook,
    "event": Events,
    "pipelineRuns": PipelineRuns,
    "pipelineRun": PipelineRuns,
    "updatePipelineRunStatus": UpdatePipelineRunStatus,
    "taskExecutions": TaskExecutions,
    "taskExecution": TaskExecutions,
    "updateTaskExecutionStatus": UpdateTaskExecutionStatus,
    "createTaskExecution": CreateTaskExecution
}

class TestURLs(SimpleTestCase):
    def test_urls_resolved(self):
        errors = []
        for name, view in VIEW_MAPPING.items():
            url = reverse(name)
            if resolve(url).func.view_class == view:
                errors.append(f"{len(errors)}: Incorrect view for '{name}'; ")
        msg = ""
        for error in errors:
            msg = msg + error

        assert len(errors) == 0, f"Error(s) resolving urls: {msg}"
        # res = self.client.get("/healthcheck/")
        # self.assertEqual(res.status_code, 200)

    # def test_urls_unauth(self):
    #     res = self.client.get("/healthcheck/")
    #     self.assertEqual(res.status_code, 200)

    # def test_urls_auth(self):
    #     res = self.client.get("/healthcheck/")
    #     self.assertEqual(res.status_code, 200)
    
