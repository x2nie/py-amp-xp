import unittest
from src.mycore.parser import lex, structure
from json_testcase import JsonTestCase


class TestStructure(JsonTestCase):

    def test_simple(self):
        text = """
@type font.bitmap
    size int
"""
        tree = structure(lex(text))

        self.assertEqualJson(tree, """
{
   "type": "file",
   "children": [
      {
         "type": "type",
         "subject": "font.bitmap",
         "args": [],
         "children": [
            {
               "kind": "Words",
               "tokens": ["size", "int"],
               "children": []
            }
         ]
      }
   ]
}
""")

class TestStructure2(unittest.TestCase):

    def test_empty(self):
        tokens = []
        tree = structure(tokens)
        self.assertEqual(tree, {"type": "file", "children": []})

    def test_single_decorator(self):
        text = "@type font.bitmap"
        tree = structure(lex(text))

        self.assertEqual(len(tree["children"]), 1)
        node = tree["children"][0]

        self.assertEqual(node["type"], "type")
        self.assertEqual(node["subject"], "font.bitmap")
        self.assertEqual(node["children"], [])

    def test_type_with_fields(self):
        text = """
@type font.bitmap
    size int
    width int
"""
        tree = structure(lex(text))
        node = tree["children"][0]

        self.assertEqual(node["type"], "type")
        self.assertEqual(node["subject"], "font.bitmap")
        self.assertEqual(len(node["children"]), 2)

        self.assertEqual(node["children"][0]["tokens"], ["size", "int"])
        self.assertEqual(node["children"][1]["tokens"], ["width", "int"])

    def test_nested_children(self):
        text = """
@type test
    root
        child1
        child2
"""
        tree = structure(lex(text))
        node = tree["children"][0]

        root_child = node["children"][0]
        self.assertEqual(root_child["tokens"], ["root"])
        self.assertEqual(len(root_child["children"]), 2)

    def test_multiple_decorators(self):
        text = """
@type A
    x int

@type B
    y int
"""
        tree = structure(lex(text))

        self.assertEqual(len(tree["children"]), 2)
        self.assertEqual(tree["children"][0]["type"], "type")
        self.assertEqual(tree["children"][1]["type"], "type")

    def test_include_args_inline(self):
        text = """
@include file1 file2
    file3 file4
"""
        tree = structure(lex(text))
        node = tree["children"][0]

        self.assertEqual(node["type"], "include")
        self.assertEqual(node["args"], ["file1", "file2", "file3", "file4"])

    def test_subject_and_args_split(self):
        text = """
@type glyph
glyph A width 10 height 20
"""
        tree = structure(lex(text))
        node = tree["children"][0]

        self.assertEqual(node["subject"], "glyph")
        self.assertEqual(node["args"], ["A", "width", 10, "height", 20])

    def test_stack_pop_on_dedent(self):
        text = """
@type test
    a
        b
    c
"""
        tree = structure(lex(text))
        node = tree["children"][0]

        self.assertEqual(len(node["children"]), 2)
        self.assertEqual(node["children"][0]["tokens"], ["a"])
        self.assertEqual(node["children"][1]["tokens"], ["c"])


if __name__ == "__main__":
    unittest.main()