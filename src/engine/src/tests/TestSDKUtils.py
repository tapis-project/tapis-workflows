import unittest

from owe_python_sdk.utils import select_field


class TestSDKUtils(unittest.TestCase):

    def testSelectField(self):
        # Providing no field selectors should just return the object
        self.assertTrue(select_field({}, []) == {})
        self.assertTrue(select_field(1, []) == 1)

        obj = {
            "key": [
                "arr_item",
                {
                    "shallow_key": "shallow_value",
                    "deep_key": {
                        "deeper_key": "deeper_value"
                    }
                }
            ]
        }
        self.assertTrue(type(select_field(obj, ["key"])) == list)
        self.assertTrue(select_field(obj, ["key", 0]) == "arr_item")
        self.assertTrue(select_field(obj, ["key", 1, "shallow_key"]) == "shallow_value")
        self.assertTrue(select_field(obj, ["key", 1, "deep_key", "deeper_key"]) == "deeper_value")

        # Must throw type error if object provided is not of type dict or list
        self.assertRaises(TypeError, lambda: select_field(1, ["test"]))

        # Must throw index error if attempting to access a non-existent index
        # In the case below, there is no 3rd item in the list
        self.assertRaises(IndexError, lambda: select_field(obj, ["key", 2]))

        arr = [
            "arr_item",
            {"key": "value"}
        ]
        self.assertTrue(select_field(arr, [0]) == "arr_item")
        self.assertTrue(select_field(arr, [1, "key"]) == "value")

if __name__ == "__main__":
    unittest.main()



