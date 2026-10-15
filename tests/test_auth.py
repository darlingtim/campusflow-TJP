import unittest
from unittest.mock import patch

from campusflow.auth import login_user, register_user


class TestAuth(unittest.TestCase):
    def test_register_returns_user_and_uses_next_available_id(self):
        users = [
            {"id": "U001", "username": "first"},
            {"id": "U003", "username": "third"},
        ]
        original_users = list(users)

        with patch("campusflow.auth.load_users", return_value=users):
            with patch("campusflow.auth.save_users") as save_users:
                with patch(
                    "builtins.input",
                    side_effect=["Ada Lovelace", "ada", "secret"],
                ):
                    user = register_user()

        self.assertEqual(user["id"], "U004")
        self.assertEqual(user["role"], "student_fellow")
        save_users.assert_called_once_with(original_users + [user])

    def test_login_returns_user_record(self):
        user = {
            "id": "U001",
            "name": "Ada Lovelace",
            "username": "ada",
            "password": "secret",
            "role": "student_fellow",
        }

        with patch("campusflow.auth.load_users", return_value=[user]):
            with patch("builtins.input", side_effect=[" ADA ", "secret"]):
                self.assertIs(login_user(), user)


if __name__ == "__main__":
    unittest.main()