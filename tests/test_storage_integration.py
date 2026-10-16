import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from campusflow import read_ticket_file, save_ticket, update_ticket
from campusflow.assign import assign_ticket
from campusflow.create_tickets import raise_ticket
from campusflow.list_view import get_ticket


@contextmanager
def temporary_ticket_store():
    with tempfile.TemporaryDirectory() as directory:
        current_directory = os.getcwd()
        os.chdir(directory)
        try:
            with open("tickets.json", "w") as tickets_file:
                json.dump([], tickets_file)
            yield directory
        finally:
            os.chdir(current_directory)


class TestTicketStorageIntegration(unittest.TestCase):
    def test_create_assign_lookup_and_read_round_trip(self):
        with temporary_ticket_store():
            with patch(
                "builtins.input",
                side_effect=["Wi-Fi outage", "Network", "high", "12", ""],
            ):
                raise_ticket()

            with patch("builtins.input", side_effect=["T001", "Ada"]):
                assign_ticket()

            with patch("builtins.input", return_value="T001"):
                with patch("campusflow.list_view.pprint") as printed:
                    get_ticket()

            stored = read_ticket_file()
            self.assertEqual(stored[0]["id"], "T001")
            self.assertEqual(stored[0]["priority"], "critical")
            self.assertEqual(stored[0]["assigned_to"], "Ada")
            printed.assert_called_once_with(stored[0])

    def test_missing_store_reads_as_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            current_directory = os.getcwd()
            os.chdir(directory)
            try:
                self.assertEqual(read_ticket_file(), [])
                self.assertTrue(os.path.isfile("tickets.json"))
                with open("tickets.json") as tickets_file:
                    self.assertEqual(json.load(tickets_file), [])
            finally:
                os.chdir(current_directory)

    def test_update_missing_ticket_reports_failure_and_preserves_file(self):
        with temporary_ticket_store():
            save_ticket({"id": "T001", "status": "open"})
            self.assertEqual(update_ticket({"id": "T999", "status": "closed"}), "update failed")
            self.assertEqual(read_ticket_file(), [{"id": "T001", "status": "open"}])


if __name__ == "__main__":
    unittest.main()
