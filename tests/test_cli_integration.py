import unittest
from unittest.mock import patch

import main


class TestMainMenu(unittest.TestCase):
    def test_exit_option_stops_menu(self):
        with patch("builtins.input", return_value="8"):
            with patch("builtins.print") as printed:
                main.main()

        printed.assert_any_call("You have exited the application.")

    def test_invalid_option_is_reported_then_exit(self):
        with patch("builtins.input", side_effect=["invalid", "8"]):
            with patch("builtins.print") as printed:
                main.main()

        printed.assert_any_call("Invalid option.")


if __name__ == "__main__":
    unittest.main()
