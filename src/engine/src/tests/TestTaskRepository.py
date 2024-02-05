import unittest

from unittest.mock import Mock

from core.repositories import TaskRepository


class TestTaskRepository(unittest.TestCase):
    def setUp(self):
        mapper = Mock()
        self.task_repo = TaskRepository(mapper)

    def testGetById(self):
        pass

if __name__ == "__main__":
    unittest.main()



