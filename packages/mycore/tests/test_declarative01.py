import unittest
from src.mycore.parser import lex, structure, declarative
from json_testcase import JsonTestCase


class TestDeclarative(JsonTestCase):

    def test_type_registry(self):
        text = """
        @type
        font.bitmap
            size int
            width int
        """
        ast = declarative(structure(lex(text)))

        self.assertEqualJson(ast["registry"], """
        {
            "font.bitmap": {
                "size": ["int"],
                "width": ["int"]
            }
        }
        """)

    def test_simple_object(self):
        text = """
        @type
        glyph
            width int
            height int

        @glyph
        A width 10 height 20
        """
        ast = declarative(structure(lex(text)))

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "name": "A",
                "props": {
                    "width": [10],
                    "height": [20]
                },
                "children": []
            }
        ]
        """)

    def test_child_mapping(self):
        text = """
        @type
        glyph
            width int
            height int

        @glyph
        A width 10 height 20
            B width 5 height 6
            C width 7 height 8
        """
        ast = declarative(structure(lex(text)))

        self.assertEqualJson(ast["children"][0]["children"], """
        [
            {
                "type": "glyph.child",
                "target": "B",
                "props": {
                    "width": [5],
                    "height": [6]
                },
                "children": []
            },
            {
                "type": "glyph.child",
                "target": "C",
                "props": {
                    "width": [7],
                    "height": [8]
                },
                "children": []
            }
        ]
        """)

    def test_ignore_unknown_type(self):
        text = """
        @unknown
        something
        """
        ast = declarative(structure(lex(text)))

        self.assertEqualJson(ast["children"], "[]")

    def test_include(self):
        text = """
                @include
                file1 file2 file3
                """
        text = """
        @include
            file1 file2 file3
        """
        ast = declarative(structure(lex(text)))

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "include",
                "children": ["file1", "file2", "file3"]
            }
        ]
        """)

    def test_skin_passthrough(self):
        text = """
        @skin
        darkmode
        """
        ast = declarative(structure(lex(text)))

        self.assertEqual(len(ast["children"]), 1)
        self.assertEqual(ast["children"][0]["type"], "skin")

    def test_arity_handling(self):
        text = """
        @type
        box
            pos int int
            size int int

        @box
        A pos 10 20 size 100 200
        """
        ast = declarative(structure(lex(text)))

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "box",
                "name": "A",
                "props": {
                    "pos": [10, 20],
                    "size": [100, 200]
                },
                "children": []
            }
        ]""")