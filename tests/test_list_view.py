import unittest
from unittest.mock import patch

from campusflow.list_view import get_ticket, list_tickets


class TestListView(unittest.TestCase):
    def test_list_tickets_reads_and_prints_tickets(self):
        tickets = [{"id": "T001", "title": "Internet is down"}]
        with patch("campusflow.list_view.read_ticket_file", return_value=tickets):
            with patch("campusflow.list_view.pprint") as printed:
                result = list_tickets()

        printed.assert_called_once_with(tickets)

    def test_get_ticket_returns_matching_ticket(self):
        tickets = [{"id": "T001"}, {"id": "T002"}]
        with patch("campusflow.list_view.read_ticket_file", return_value=tickets):
            with patch("builtins.input", return_value="T002"):
                with patch("campusflow.list_view.pprint") as printed:
                    get_ticket()

        printed.assert_called_once_with(tickets[1])

    def test_get_ticket_does_not_stop_before_later_match(self):
        tickets = [{"id": "T001"}, {"id": "T002"}]
        with patch("campusflow.list_view.read_ticket_file", return_value=tickets):
            with patch("builtins.input", return_value="T002"):
                with patch("campusflow.list_view.pprint"):
                    get_ticket()

    def test_get_ticket_rejects_missing_ticket(self):
        with patch("campusflow.list_view.read_ticket_file", return_value=[{"id": "T001"}]):
            with patch("builtins.input", return_value="T999"):
                with self.assertRaisesRegex(ValueError, "T999 was not found"):
                    get_ticket()

    def test_get_ticket_rejects_non_text_id(self):
        with patch("builtins.input", return_value=None):
            with self.assertRaisesRegex(ValueError, "Invalid ticket ID"):
                get_ticket()


if __name__ == "__main__":
    unittest.main()
