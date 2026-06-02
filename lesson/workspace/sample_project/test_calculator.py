import unittest

from calculator import add, average, divide, subtract


class CalculatorTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)

    def test_average(self):
        self.assertEqual(average([2, 4, 6]), 4)

    def test_divide_by_zero_message(self):
        with self.assertRaisesRegex(ValueError, "zero"):
            divide(1, 0)


if __name__ == "__main__":
    unittest.main()

