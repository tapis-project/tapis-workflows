import unittest


class TestImports(unittest.TestCase):
    def testETLImports(self):
        from backend.views.http.tapis_etl import (
            RemoteInbox,
            RemoteOutbox,
            LocalInbox,
            LocalOutbox
        )

    def testTapisETLImports(self):
        from backend.views.http.tapis_etl import TapisETLPipeline

if __name__ == "__main__":
    unittest.main()


