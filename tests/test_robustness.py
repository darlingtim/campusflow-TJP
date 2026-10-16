import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from campusflow import _load_tickets, load_users, read_ticket_file
from campusflow.auth import get_current_user, login_user, logout_user
from campusflow.create_tickets import Ticket, generate_ticket_id
from campusflow.notes import Note, generate_note_id, get_visible_notes
from campusflow.validate_note import validate_note
from campusflow.validate_ticket import TicketValidationError


class TestSystemRobustness(unittest.TestCase):
    # 1. Ticket and note ID generation tolerates malformed stored IDs
    def test_ticket_and_note_id_generation_tolerates_malformed_ids(self):
        malformed_tickets = [
            {"id": None},
            {"id": ""},
            {"id": "bad-id"},
            {"id": "Txyz"},
            {"id": "N005"},
            {"id": "T003"},
            {"id": "T015"},
        ]
        with patch("campusflow.create_tickets.read_ticket_file", return_value=malformed_tickets):
            self.assertEqual(generate_ticket_id(), "T016")

        ticket_with_malformed_notes = {
            "id": "T001",
            "notes": [
                {"id": None},
                {"id": ""},
                {"id": "bad"},
                {"id": "T005"},
                {"id": "Nabc"},
                {"id": "N007"},
                {"id": "N012"},
            ],
        }
        self.assertEqual(generate_note_id(ticket_with_malformed_notes), "N013")

    # 2. Missing, empty, and malformed ticket/user JSON files are safely handled
    def test_missing_empty_and_malformed_json_files_handled_safely(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            orig_dir = os.getcwd()
            os.chdir(temp_dir)
            try:
                # Missing files
                self.assertEqual(_load_tickets("non_existent_tickets.json"), [])
                self.assertEqual(load_users(), [])

                # Empty files (0 bytes)
                Path("tickets.json").write_text("", encoding="utf-8")
                Path("users.json").write_text("", encoding="utf-8")
                self.assertEqual(read_ticket_file(), [])
                self.assertEqual(load_users(), [])

                # Malformed JSON files (syntax errors)
                Path("tickets.json").write_text("{ broken json ...", encoding="utf-8")
                Path("users.json").write_text("[ not valid json", encoding="utf-8")
                self.assertEqual(read_ticket_file(), [])
                self.assertEqual(load_users(), [])
            finally:
                os.chdir(orig_dir)

    # 3. Successful and failed authentication correctly updates the current-user state
    def test_authentication_updates_current_user_state(self):
        users_db = [
            {
                "id": "U001",
                "name": "Ada Lovelace",
                "username": "ada",
                "password": "secure123",
                "role": "support_lead",
            },
            {
                "id": "U002",
                "name": "Charles Babbage",
                "username": "charles",
                "password": "password456",
                "role": "student_fellow",
            },
        ]
        logout_user()
        self.assertIsNone(get_current_user())

        with patch("campusflow.auth.load_users", return_value=users_db):
            # Failed login (wrong password)
            res_fail = login_user("ada", "wrong_pass")
            self.assertIsNone(res_fail)
            self.assertIsNone(get_current_user())

            # Failed login (unknown username)
            res_unknown = login_user("unknown_user", "secure123")
            self.assertIsNone(res_unknown)
            self.assertIsNone(get_current_user())

            # Successful login
            res_success = login_user("ada", "secure123")
            self.assertEqual(res_success, users_db[0])
            self.assertEqual(get_current_user(), users_db[0])

            # Logout clears session
            logout_user()
            self.assertIsNone(get_current_user())

    # 4. Shared-note visibility is restricted to ticket creator, assigned user, or support lead
    def test_shared_note_permission_restricted_to_creator_assigned_or_support_lead(self):
        ticket = {
            "id": "T001",
            "status": "open",
            "created_by": "U002",
            "assigned_to": "U001",
            "notes": [],
        }

        creator_user = {"id": "U002", "name": "Charles", "role": "student_fellow"}
        assigned_user = {"id": "U001", "name": "Ada", "role": "support_staff"}
        lead_user = {"id": "U099", "name": "Grace", "role": "support_lead"}
        unrelated_student = {"id": "U003", "name": "John", "role": "student_fellow"}
        unrelated_staff = {"id": "U004", "name": "Bob", "role": "support_staff"}

        # Ticket creator can add shared note
        res_creator = validate_note(ticket, creator_user, "Creator adding details")
        self.assertEqual(res_creator["author"], "Charles")
        self.assertEqual(res_creator["visibility"], "shared")

        # Assigned staff can add note
        res_assigned = validate_note(
            ticket, assigned_user, "Assigned staff update", visibility="shared"
        )
        self.assertEqual(res_assigned["author"], "Ada")
        self.assertEqual(res_assigned["visibility"], "shared")

        # Support lead can add note even if neither creator nor assigned
        res_lead = validate_note(
            ticket, lead_user, "Lead triage comment", visibility="shared"
        )
        self.assertEqual(res_lead["author"], "Grace")
        self.assertEqual(res_lead["visibility"], "shared")

        # Unrelated student cannot add a note
        with self.assertRaisesRegex(
            TicketValidationError,
            "Only the ticket creator or assigned staff member can add a note.",
        ):
            validate_note(ticket, unrelated_student, "Random student trying to note")

        # Unrelated staff cannot add a note to a ticket assigned to someone else
        with self.assertRaisesRegex(
            TicketValidationError,
            "Only the assigned staff member can add a note.",
        ):
            validate_note(ticket, unrelated_staff, "Unassigned staff trying to note")


if __name__ == "__main__":
    unittest.main()