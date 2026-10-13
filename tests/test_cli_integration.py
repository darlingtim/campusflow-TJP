import unittest
from unittest.mock import patch

import main
from campusflow.validate_ticket import TicketValidationError


class TestMainMenu(unittest.TestCase):
    def test_exit_option_stops_menu(self):
        with patch("builtins.input", return_value="8"):
            with patch("builtins.print") as printed:
                main.main()

        printed.assert_any_call("\nYou have exited the application.")

    def test_invalid_option_is_reported_then_exit(self):
        with patch("builtins.input", side_effect=["invalid", "8"]):
            with patch("builtins.print") as printed:
                main.main()

        printed.assert_any_call(
            "\nError:\n    Invalid option. please select a valid option from the menu."
        )

    def test_validation_error_is_reported_then_menu_continues(self):
        with patch("builtins.input", side_effect=["1", "8"]):
            with patch("main.raise_ticket", side_effect=TicketValidationError(
                "Ticket title cannot be empty.\nTicket category cannot be empty."
            )):
                with patch("builtins.print") as printed:
                    main.main()

        printed.assert_any_call("\nError Message:")
        printed.assert_any_call("    Ticket title cannot be empty.")
        printed.assert_any_call("    Ticket category cannot be empty.")
        printed.assert_any_call("\nYou have exited the application.")


if __name__ == "__main__":
    unittest.main()
