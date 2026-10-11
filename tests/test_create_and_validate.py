import unittest
from unittest.mock import patch

from campusflow.create_tickets import Ticket, generate_ticket_id, raise_ticket
from campusflow.validate_ticket import TicketValidationError, validate_ticket


class TestTicket(unittest.TestCase):
    def test_priority_boundaries(self):
        cases = [
            ("high", "10", "critical"),
            ("high", "9", "high"),
            ("medium", "1", "medium"),
            ("low", "10", "high"),
            ("low", "2", "low"),
        ]
        for urgency, affected_users, expected in cases:
            with self.subTest(urgency=urgency, affected_users=affected_users):
                self.assertEqual(
                    Ticket("T001", "Title", "Other", urgency, affected_users).priority,
                    expected,
                )

    def test_to_dict_contains_new_ticket_defaults(self):
        ticket = Ticket("T001", "Title", "Other", "low", "1")
        self.assertEqual(ticket.to_dict()["status"], "open")
        self.assertIsNone(ticket.to_dict()["assigned_to"])

    def test_invalid_numeric_input_can_be_validated(self):
        ticket = Ticket("T001", "Title", "Other", "low", "not-a-number")
        self.assertIn("Affected users must be a valid whole number.", validate_ticket(ticket))

    def test_validation_reports_all_invalid_fields(self):
        ticket = Ticket("T001", " ", "Unknown", "urgent", "0")
        errors = validate_ticket(ticket)
        self.assertEqual(len(errors), 4)
        self.assertIn("Ticket title cannot be empty.", errors)
        self.assertIn("Category must be Network, Hardware, Software, or Other.", errors)
        self.assertIn("Urgency must be low, medium, or high.", errors)
        self.assertIn("Affected users must be greater than zero.", errors)

    def test_validation_accepts_case_and_whitespace(self):
        ticket = Ticket("T001", "Title", " network ", "HIGH", " 3 ")
        self.assertEqual(validate_ticket(ticket), [])

    def test_generate_ticket_id_uses_highest_existing_id(self):
        tickets = [{"id": "T002"}, {"id": "T010"}, {"id": "T003"}]
        with patch("campusflow.create_tickets.read_ticket_file", return_value=tickets):
            self.assertEqual(generate_ticket_id(), "T011")

    def test_generate_first_ticket_id_for_empty_file(self):
        with patch("campusflow.create_tickets.read_ticket_file", return_value=[]):
            self.assertEqual(generate_ticket_id(), "T001")

    def test_raise_ticket_rejects_invalid_input_without_saving(self):
        answers = ["", "Other", "low", "0"]
        with patch("builtins.input", side_effect=answers):
            with patch("campusflow.create_tickets.save_ticket") as save:
                with self.assertRaises(TicketValidationError):
                    raise_ticket()
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
