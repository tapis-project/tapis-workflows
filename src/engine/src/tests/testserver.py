import sys
import unittest

from unittest.mock import patch


class TestServer(unittest.TestCase):
    def testServerInit(self, pika):
        pass
        # sys.modules["pika"] = __import__('mock_B')
        # from core.Server import Server


        # self.server = Server()
        # self.assertEqual(self.server, type(Server))

if __name__ == "__main__":
    unittest.main()