import unittest


class TestImports(unittest.TestCase):
    def testETLImports(self):
        import backend.views.http.etl

    def testTapisETLImports(self):
        import backend.views.http.tapis_etl

if __name__ == "__main__":
    unittest.main()


