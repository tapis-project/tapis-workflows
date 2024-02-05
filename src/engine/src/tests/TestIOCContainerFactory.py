import unittest

from core.ioc import IOCContainerFactory
from core.daos import WorkflowExecutorStateDAO


class TestIOCContainerFactory(unittest.TestCase):
    def setUp(self):
        self.container_factory = IOCContainerFactory()
        self.container = self.container_factory.build()

    def testLoad(self):
        obj = self.container.load("WorkflowExecutorStateDAO")
        self.assertEqual(type(obj), WorkflowExecutorStateDAO)

    def testLoadTransient(self):
        obj1 = self.container.load("WorkflowExecutorStateDAO")
        obj2 = self.container.load("WorkflowExecutorStateDAO")
        self.assertNotEqual(id(obj1), id(obj2))
    
    def testLoadSingleton(self):
        obj1 = self.container.load("ReactiveState")
        obj2 = self.container.load("ReactiveState")
        self.assertEqual(id(obj1), id(obj2))

if __name__ == "__main__":
    unittest.main()


