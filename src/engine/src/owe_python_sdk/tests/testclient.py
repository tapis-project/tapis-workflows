import unittest


from tests.fixtures.valid_tasks import image_build, request
from client import Task


class TestTask(unittest.TestCase):
    def testImageBuild(self):
        self.assertEqual(type(Task(image_build)), Task)

    def testRequest(self):
        self.assertEqual(type(Task(request)), Task)

if __name__ == "__main__":
    unittest.main()