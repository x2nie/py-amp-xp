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
                "subject": "A",
                "line": 8,
                 "args": [
                    "width",
                    10,
                    "height",
                    20
                ],
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
        # ast = resolve(ast, ast["registry"])


        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "subject": "A",
                "args": ["width", 10, "height", 20],
                "line": 8,
                "children": []
            },
            {
                "type": "glyph",
                "subject": "B",
                "args": ["width", 5, "height", 6],
                "line": 9,
                "children": []
            },
            {
                "type": "glyph",
                "subject": "C",
                "args": ["width", 7, "height", 8],
                "line": 10,
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

        self.assertEqualJson(ast["children"], """[
            {
                "args": [],
                "children": [],
                "subject": "something",
                "type": "unknown",
                "line": 3
            }
        ]""")

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

    def test_multi_button_instances(self):
        text = """
        @type
        button
            at int int

        @button
        btnPlay at 16 88
        btnPause at 39 88
        btnStop at 62 88
        """

        ast = declarative(structure(lex(text)))

        self.assertEqual(len(ast["children"]), 3)
    
        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "button",
                "subject": "btnPlay",
                "args": ["at", 16, 88],
                "line": 7,
                "children": []
            },
            {
                "type": "button",
                "subject": "btnPause",
                "args": ["at", 39, 88],
                "line": 8,
                "children": []
            },
            {
                "type": "button",
                "subject": "btnStop",
                "args": ["at", 62, 88],
                "line": 9,
                "children": []
            }
        ]
        """)
        
    # def test_arity_handling(self):
    #     text = """
    #     @type
    #     box
    #         pos int int
    #         size int int

    #     @box
    #     A pos 10 20 size 100 200
    #     """
    #     ast = declarative(structure(lex(text)))

    #     self.assertEqualJson(ast["children"], """
    #     [
    #         {
    #             "type": "box",
    #             "name": "A",
    #             "props": {
    #                 "pos": [10, 20],
    #                 "size": [100, 200]
    #             },
    #             "children": []
    #         }
    #     ]""")