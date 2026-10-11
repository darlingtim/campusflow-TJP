import unittest
from unittest.mock import patch

from campusflow.assign import assign_ticket


class TestAssignTicket(unittest.TestCase):
    def test_assigns_existing_ticket_and_persists_it(self):
        tickets = [{"id": "T001", "assigned_to": None}]
        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.update_ticket", return_value="update success") as update:
                with patch("builtins.input", side_effect=["T001", "  Ada  "]):
                    result = assign_ticket()

        self.assertIsNone(result)
        self.assertEqual(tickets[0]["assigned_to"], "Ada")
        update.assert_called_once_with(tickets[0])

    def test_blank_staff_name_is_rejected_before_file_access(self):
        with patch("builtins.input", side_effect=["T001", "  "]):
            with self.assertRaises(ValueError):
                assign_ticket()

    def test_unknown_ticket_is_reported(self):
        with patch("campusflow.assign.read_ticket_file", return_value=[]):
            with patch("builtins.input", side_effect=["T999", "Ada"]):
                with patch("builtins.print") as printed:
                    assign_ticket()

        printed.assert_called_once_with("\nTicket T999 was not found.")


if __name__ == "__main__":
    unittest.main()
