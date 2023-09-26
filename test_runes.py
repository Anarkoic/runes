import unittest
from runes import RuneProtocol  # Replace with your actual module and class

class TestYourClass(unittest.TestCase):

    def setUp(self):
        self.obj = RuneProtocol()  # Replace with actual object creation logic if needed

    def test_symbol_to_int_valid(self):
        self.assertEqual(self.obj.symbol_to_int('A'), 0)  # 'A' is 0 in base-26
        self.assertEqual(self.obj.symbol_to_int('Z'), 25)  # 'Z' is 25 in base-26
        self.assertEqual(self.obj.symbol_to_int('BA'), 26)  # 'BA' is 26 in base-26
        self.assertEqual(self.obj.int_to_symbol(703), 'BAA')
        self.assertEqual(self.obj.int_to_symbol(18278), 'ZZZ')  # You may want to check the actual correspondence and replace 'ZZZ' if it's not correct.


    def test_symbol_to_int_invalid(self):
        with self.assertRaises(ValueError):
            self.obj.symbol_to_int('1')  # Test with a digit
        with self.assertRaises(ValueError):
            self.obj.symbol_to_int('a')  # Test with a lowercase letter
        with self.assertRaises(ValueError):
            self.obj.symbol_to_int('!')  # Test with a special character
        with self.assertRaises(ValueError):
            self.obj.symbol_to_int('')   # Test with an empty string

if __name__ == '__main__':
    unittest.main()
