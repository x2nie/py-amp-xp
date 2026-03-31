from src.mycore.parser import lex, structure, declarative, resolve, resolve_include
from json_testcase import JsonTestCase


class FakeLoader:
    def __init__(self, files):
        self.files = files

    def __call__(self, path):
        if path not in self.files:
            raise Exception(f"File not found: {path}")
        return self.files[path]


class TestResolveSemantic(JsonTestCase):

    def pipeline(self, text, loader=None):
        ast = declarative(structure(lex(text)))

        if loader:
            ast = resolve_include(ast, loader)

        return resolve(ast, ast["registry"])


    def test_simple_props(self):
        text = """
        @type
        glyph
            width int
            height int

        @glyph
        A width 10 height 20
        """

        ast = self.pipeline(text)

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "name": "A",
                "props": {
                    "width": [10],
                    "height": [20]
                },
                "children": [],
                "schema": {
                    "width": ["int"],
                    "height": ["int"]
                }
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

        ast = self.pipeline(text)

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


    def test_arity(self):
        text = """
        @type
        box
            pos int int
            size int int

        @box
        A pos 10 20 size 100 200
        """

        ast = self.pipeline(text)

        self.assertEqualJson(ast["children"][0]["props"], """
        {
            "pos": [10, 20],
            "size": [100, 200]
        }
        """)


    def test_include_then_resolve(self):
        files = {
            "B.dsl": """
            @type
            glyph
                width int

            @glyph
            B width 5
            """
        }

        loader = FakeLoader(files)

        text = """
        @include
        B.dsl
        """

        ast = self.pipeline(text, loader)

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "name": "B",
                "props": {
                    "width": [5]
                },
                "children": [],
                "schema": {
                    "width": ["int"]
                }
            }
        ]
        """)


    def test_forward_reference(self):
        files = {
            "B.dsl": """
            @type
            glyph
                width int
            """
        }

        loader = FakeLoader(files)

        text = """
        @glyph
        A width 10

        @include
        B.dsl
        """

        ast = self.pipeline(text, loader)

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "name": "A",
                "props": {
                    "width": [10]
                },
                "children": [],
                "schema": {
                    "width": ["int"]
                }
            }
        ]
        """)


    def test_unknown_property(self):
        text = """
        @type
        glyph
            width int

        @glyph
        A widht 10
        """

        ast = self.pipeline(text)

        # print((ast["children"][0]["errors"]), 1)
        # self.assertEqual(repr(ast["children"][0]["errors"]), 1)
        #  [{'message': 'Unknown property: widht', 'foo': 3, 'line': 6}, {'message': 'Unknown property: 10', 'foo': 3, 'line': 6}] 1
        self.assertEqual(len(ast["children"][0]["errors"]), 2)

    def test_missing_value(self):
        text = """
        @type
        glyph
            width int

        @glyph
        A width
        """

        ast = self.pipeline(text)

        self.assertEqual(len(ast["children"][0]["errors"]), 1)        

    def test_unknown_type(self):
        text = """
        @unknown
        A x 1
        """

        ast = self.pipeline(text)

        self.assertEqual(len(ast["children"][0]["errors"]), 1)