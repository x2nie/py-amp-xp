import unittest
from src.mycore.parser import lex


class TestLex(unittest.TestCase):

    def test_empty_lines_ignored(self):
        text = "\n\n   \n"
        result = lex(text)
        self.assertEqual(result, [])

    def test_basic_words(self):
        text = "hello world"
        result = lex(text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["kind"], "Words")
        self.assertEqual(result[0]["tokens"], ["hello", "world"])
        self.assertEqual(result[0]["indent"], 0)

    def test_number_parsing(self):
        text = "x 10 20"
        result = lex(text)

        self.assertEqual(result[0]["tokens"], ["x", 10, 20])

    def test_indent_detection(self):
        text = "    a b\n        c d"
        result = lex(text)

        self.assertEqual(result[0]["indent"], 1)
        self.assertEqual(result[1]["indent"], 2)

    def test_decorator(self):
        text = "@type font.bitmap"
        result = lex(text)

        self.assertEqual(result[0]["kind"], "Decorator")
        self.assertEqual(result[0]["name"], "type")
        self.assertEqual(result[0]["args"], ["font.bitmap"])

    def test_comment_stripped(self):
        text = 'a b c " ini komentar'
        result = lex(text)

        self.assertEqual(result[0]["tokens"], ["a", "b", "c"])

    def test_mixed_lines(self):
        text = """
@type font.bitmap
    size int
    width int

glyph A width 10
        """

        result = lex(text)

        self.assertEqual(len(result), 4)

        self.assertEqual(result[0]["kind"], "Decorator")
        self.assertEqual(result[1]["tokens"], ["size", "int"])
        self.assertEqual(result[2]["tokens"], ["width", "int"])
        self.assertEqual(result[3]["tokens"], ["glyph", "A", "width", 10])


if __name__ == "__main__":
    unittest.main()