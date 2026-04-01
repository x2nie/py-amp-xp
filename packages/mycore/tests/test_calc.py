import unittest
from src.calc import discount

class TestCalc(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(discount(100, 10), 90)

if __name__ == "__main__":
    unittest.main()
