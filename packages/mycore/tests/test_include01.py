from src.mycore.parser import lex, structure, declarative, resolve_include
from json_testcase import JsonTestCase, FakeLoader


class TestResolveInclude(JsonTestCase):

    def test_simple_include(self):
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

        ast = declarative(structure(lex(text)))
        ast = resolve_include(ast, loader)

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "name": "B",
                "props": {
                    "width": [5]
                },
                "children": []
            }
        ]
            """)

    def test_include_merge_registry(self):
        files = {
            "B.dsl": """
                @type
                glyph
                    width int
                """
        }

        loader = FakeLoader(files)

        text = """
            @include
                B.dsl
            """

        ast = declarative(structure(lex(text)))
        ast = resolve_include(ast, loader)

        self.assertEqualJson(ast["registry"], """
            {
                "glyph": {
                    "width": ["int"]
                }
            }
            """)

    def test_nested_include(self):
        files = {
            "B.dsl": 
                """
                @include
                    C.dsl
                """,
            "C.dsl": """
                @type
                glyph
                    width int

                @glyph
                C width 7
                """
        }

        loader = FakeLoader(files)

        text = """
        @include
            B.dsl
        """

        ast = declarative(structure(lex(text)))
        ast = resolve_include(ast, loader)

        self.assertEqualJson(ast["children"], """
        [
            {
                    "type": "glyph",
                    "name": "C",
                    "props": {
                        "width": [7]
                    },
                    "children": []
            }
        ]
        """)

    def test_circular_include(self):
        files = {
            "A.dsl": "@include\nB.dsl",
            "B.dsl": "@include\nA.dsl",
        }

        loader = FakeLoader(files)

        text = """
@include
    A.dsl
"""

        ast = declarative(structure(lex(text)))

        with self.assertRaises(Exception):
            resolve_include(ast, loader)

    def test_include_with_existing_content(self):
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

        @glyph
        A width 10
        """

        ast = declarative(structure(lex(text)))
        ast = resolve_include(ast, loader)

        self.assertEqualJson(ast["children"], """
        [
            {
                "type": "glyph",
                "name": "B",
                "props": {
                    "width": [5]
                },
                "children": []
            },
            {
                "type": "glyph",
                "name": "A",
                "props": {
                    "width": [10]
                },
                "children": []
            }
        ]
        """)