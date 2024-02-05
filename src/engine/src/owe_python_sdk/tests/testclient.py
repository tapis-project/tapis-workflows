import unittest

from tests.fixtures.tasks import image_build, request
from tests.fixtures.pipelines import standard_workflow
from client import Task, Pipeline, Runner


class TestRunner(Runner):
    def __init__(self):
        Runner.__init__(self)

    def submit(self, request: dict):
        self._client.workflows.runPipeline(**request)

    class Config:
        prompt_missing = True
        env = {
            "TAPIS_BASE_URL": {"type": str},
            "TAPIS_USERNAME": {"type": str},
            "TAPIS_PASSWORD": {"type": str, "secret": True}
        }

class TestTask(unittest.TestCase):
    def testImageBuild(self):
        self.assertEqual(type(Task(image_build)), Task)

    def testRequest(self):
        self.assertEqual(type(Task(request)), Task)

class TestPipeline(unittest.TestCase):
    def testStandardWorkflow(self):
        self.assertEqual(type(Pipeline(standard_workflow, TestRunner)), Pipeline)

if __name__ == "__main__":
    unittest.main()