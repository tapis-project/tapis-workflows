# from pprint import pprint
from src.api.src.backend.views.http.requests import FunctionTask
import json

schema = None
with open("./src/api/src/tests/fixtures/task-fn-env-params-git.json", "r") as file:
    schema = json.loads(str(file.read()))

fn = FunctionTask(**schema)

# Convert the input to json
_input = {}
for key in fn.input:
    _input[key] = fn.input[key].dict()

print(_input)

# task_props = {
#     "id": "build",
#     "type": "image_build",
#     "description": "build mpm image",
#     "builder": "kaniko",
#     "input": {
#         "from-env": {
#             "type": "string",
#             "value_from": {
#                 "env": "TEST"
#             }
#         },
#         "from-params": {
#             "type": "string",
#             "value_from": {
#                 "params": "TEST"
#             }
#         },
#         "from-task-output": {
#             "type": "string",
#             "value_from": {
#                 "task_output": {
#                     "task_id": "some-id",
#                     "output_id": "test"
#                 }
#             }
#         },
#         "from-host": {
#             "type": "string",
#             "value_from": {
#                 "host": {
#                     "type": "kubernetes_secret",
#                     "name": "some-secret-name",
#                     "field_selector": "{this.is.a.field.selector}"
#                 }
#             }
#         },
#         "from-secret": {
#             "type": "string",
#             "value_from": {
#                 "secret": {
#                     "engine": "tapis-security-kernel",
#                     "pk": "some-sk-secret-name",
#                     "field_selector": "{this.is.a.field.selector}"
#                 }
#             }
#         }
#     },
#     "context": {
#         "type": "github",
#         "url": "joestubbs/mpm",
#         "branch": "master",
#         "build_file_path": "/Dockerfile",
#         "visibility": "public"
#     },
#     "destination": {
#         "type": "dockerhub",
#         "url": "nathandf/mpm-test",
#         "tag": "test",
#         "visibility": "private",
#         "credentials": {
#             "username": "nathandf",
#             "token": "a190f902-d418-491a-9abc-c22eff2aa335"
#         }
#     },
#     "depends_on": [
        
#     ]
# }

# pipeline_props = {
#     "id": "test",
#     "tasks": [task_props]
# }


# pprint(ImageBuildTask(**task_props).input)
# print(BasePipeline(**pipeline_props))

# from src.engine.src.owe_python_sdk.client import Runner

# class TapisRunner(Runner):
#     def __init__(self):
#         Runner.__init__(self)

#     def submit(self, request: dict):
#         self._client.workflows.runPipeline(**request)

#     class Config:
#         prompt_missing = True
#         env = {
#             "TAPIS_BASE_URL": {"type": str},
#             "TAPIS_USERNAME": {"type": str},
#             "TAPIS_PASSWORD": {"type": str, "secret": True}
#         }

# TapisRunner()