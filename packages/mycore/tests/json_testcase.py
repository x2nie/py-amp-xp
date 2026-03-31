import json
import unittest


class JsonTestCase(unittest.TestCase):
    maxDiff = None  # biar diff full keluar kalau gagal

    def assertEqualJson(self, actual, expected_json_str):
        """
        Compare dict/list dengan JSON string (pretty).
        """

        try:
            expected = json.loads(expected_json_str)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON expected:\n{e}")

        actual_str = json.dumps(actual, indent=3, sort_keys=True)
        expected_str = json.dumps(expected, indent=3, sort_keys=True)

        if actual_str != expected_str:
            message = (
                "\nJSON not equal:\n\n"
                "---- ACTUAL ----\n"
                f"{actual_str}\n\n"
                "---- EXPECTED ----\n"
                f"{expected_str}\n"
            )
            self.fail(message)