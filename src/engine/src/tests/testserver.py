import unittest

from Server import Server


class TestServer(unittest.TestCase):
    def testServerInit(self):
        self.server = Server()
        self.assertEqual(type(self.server), Server)
        pass

if __name__ == "__main__":
    unittest.main()