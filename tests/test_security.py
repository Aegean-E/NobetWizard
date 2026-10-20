import unittest

from security import check_hashes, secure_equals


class SecureEqualsTest(unittest.TestCase):
    def test_compares_ascii_and_unicode_text(self):
        self.assertTrue(secure_equals("şifre", "şifre"))
        self.assertFalse(secure_equals("şifre", "sifre"))
        self.assertTrue(secure_equals("plain", "plain"))

    def test_treats_missing_values_as_text(self):
        self.assertTrue(secure_equals(None, "None"))
        self.assertTrue(secure_equals(42, "42"))


class CheckHashesTest(unittest.TestCase):
    def test_rejects_missing_or_malformed_hashes(self):
        self.assertFalse(check_hashes("password", None))
        self.assertFalse(check_hashes("password", ""))
        self.assertFalse(check_hashes("password", "not-a-bcrypt-hash"))


if __name__ == "__main__":
    unittest.main()
