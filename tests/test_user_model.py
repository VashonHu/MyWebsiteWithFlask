import unittest
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(ValueError):
            u.password
