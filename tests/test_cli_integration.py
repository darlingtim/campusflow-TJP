import unittest
from unittest.mock import patch

import main
from campusflow.validate_ticket import TicketValidationError

USER = {
    "id": "U001",
    "name": "Ada Lovelace",
    "username": "ada",
    "password": "secure123",  # nosec B105 - fixture value, never a real login
    "role": "student_fellow",
}


class TestLoginMenu(unittest.TestCase):
    def test_exit_option_stops_the_program(self):
        with patch("builtins.input", return_value="3"):
            with patch("builtins.print") as printed:
                main.main()

        printed.assert_any_call("\nYou have exited the application.")

    def test_register_option_runs_registration(self):
        with patch("builtins.input", side_effect=["1", "3"]):
            with patch("main.register_user") as register:
                with patch("builtins.print"):
                    main.main()

        register.assert_called_once_with()

    def test_registration_error_is_reported_then_menu_continues(self):
        with patch("builtins.input", side_effect=["1", "3"]):
            with patch(
                "main.register_user",
                side_effect=ValueError("Name, username, and password are required."),
            ):
                with patch("builtins.print") as printed:
                    main.main()

        printed.assert_any_call("\nError Message:")
        printed.assert_any_call("    Name, username, and password are required.")

    def test_failed_login_returns_to_the_login_menu(self):
        with patch("builtins.input", side_effect=["2", "3"]):
            with patch("main.login_user", return_value=None) as login:
                with patch("main.ticket_menu") as ticket_menu:
                    with patch("builtins.print"):
                        main.main()

        login.assert_called_once_with()
        ticket_menu.assert_not_called()

    def test_successful_login_opens_the_ticket_menu(self):
        with patch("builtins.input", side_effect=["2", "3"]):
            with patch("main.login_user", return_value=USER):
                with patch("main.ticket_menu") as ticket_menu:
                    with patch("builtins.print"):
                        main.main()

        ticket_menu.assert_called_once_with(USER)


class TestTicketMenu(unittest.TestCase):
    def test_logout_option_returns_to_the_login_menu(self):
        with patch("builtins.input", return_value="12"):
            with patch("main.logout_user") as logout:
                with patch("builtins.print"):
                    main.ticket_menu(USER)

        logout.assert_called_once_with()

    def test_search_option_runs_the_search_then_logs_out(self):
        with patch("builtins.input", side_effect=["8", "12"]):
            with patch("main.search_tickets_menu") as search:
                with patch("main.logout_user"):
                    with patch("builtins.print"):
                        main.ticket_menu(USER)

        search.assert_called_once_with()

    def test_add_follow_up_note_option_runs_the_prompt_then_logs_out(self):
        with patch("builtins.input", side_effect=["10", "12"]):
            with patch("main.add_follow_up_note") as add:
                with patch("main.logout_user"):
                    with patch("builtins.print"):
                        main.ticket_menu(USER)

        add.assert_called_once_with(USER)

    def test_view_ticket_notes_option_runs_the_view_then_logs_out(self):
        with patch("builtins.input", side_effect=["11", "12"]):
            with patch("main.view_ticket_notes") as view:
                with patch("main.logout_user"):
                    with patch("builtins.print"):
                        main.ticket_menu(USER)

        view.assert_called_once_with(USER)

    def test_invalid_option_is_reported_then_menu_continues(self):
        with patch("builtins.input", side_effect=["invalid", "12"]):
            with patch("main.logout_user"):
                with patch("builtins.print") as printed:
                    main.ticket_menu(USER)

        printed.assert_any_call(
            "\nError:\n    Invalid option. please select a valid option from the menu."
        )

    def test_raise_ticket_receives_the_logged_in_user(self):
        with patch("builtins.input", side_effect=["1", "12"]):
            with patch("main.raise_ticket") as raise_ticket:
                with patch("main.logout_user"):
                    with patch("builtins.print"):
                        main.ticket_menu(USER)

        raise_ticket.assert_called_once_with(USER)

    def test_validation_error_is_reported_then_menu_continues(self):
        with patch("builtins.input", side_effect=["1", "12"]):
            with patch("main.raise_ticket", side_effect=TicketValidationError(
                "Ticket title cannot be empty.\nTicket category cannot be empty."
            )):
                with patch("main.logout_user"):
                    with patch("builtins.print") as printed:
                        main.ticket_menu(USER)

        printed.assert_any_call("\nError Message:")
        printed.assert_any_call("    Ticket title cannot be empty.")
        printed.assert_any_call("    Ticket category cannot be empty.")

    def test_understanding_check_option_runs_the_check_then_logs_out(self):
        with patch("builtins.input", side_effect=["9", "12"]):
            with patch("main.understanding_check_menu") as check:
                with patch("main.logout_user"):
                    with patch("builtins.print"):
                        main.ticket_menu(USER)

        check.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
