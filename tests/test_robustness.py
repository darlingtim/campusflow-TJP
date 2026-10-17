import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from campusflow import _load_tickets, load_users, read_ticket_file
from campusflow.auth import get_current_user, login_user, logout_user
from campusflow.create_tickets import generate_ticket_id
from campusflow.migrate import migrate_ticket, migrate_tickets_file
from campusflow.notes import generate_note_id, get_visible_notes
from campusflow.validate_note import validate_note
from campusflow.validate_ticket import TicketStorageError, TicketValidationError


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

                # Malformed JSON files (syntax errors). A corrupt ticket store
                # is rejected rather than read as empty, so the next save
                # cannot overwrite recoverable data (Requirement E).
                Path("tickets.json").write_text("{ broken json ...", encoding="utf-8")
                Path("users.json").write_text("[ not valid json", encoding="utf-8")
                with self.assertRaises(TicketStorageError):
                    read_ticket_file()
                self.assertEqual(load_users(), [])

                # The rejected file is left exactly as it was found.
                self.assertEqual(
                    Path("tickets.json").read_text(encoding="utf-8"),
                    "{ broken json ...",
                )
            finally:
                os.chdir(orig_dir)

    def test_duplicate_ticket_ids_are_rejected_on_load(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            orig_dir = os.getcwd()
            os.chdir(temp_dir)
            try:
                Path("tickets.json").write_text(
                    json.dumps([{"id": "T001"}, {"id": "T001"}]),
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    TicketStorageError, "duplicate ticket id T001"
                ):
                    read_ticket_file()
            finally:
                os.chdir(orig_dir)

    def test_ticket_without_a_usable_id_is_rejected_on_load(self):
        cases = [
            ([{"id": None}], "without a usable id"),
            ([{"id": "  "}], "without a usable id"),
            ([{"title": "no id at all"}], "without a usable id"),
            (["not an object"], "not an object"),
            ({"id": "T001"}, "does not contain a list"),
        ]

        for records, expected in cases:
            with self.subTest(records=records):
                with tempfile.TemporaryDirectory() as temp_dir:
                    orig_dir = os.getcwd()
                    os.chdir(temp_dir)
                    try:
                        Path("tickets.json").write_text(
                            json.dumps(records), encoding="utf-8"
                        )

                        with self.assertRaisesRegex(TicketStorageError, expected):
                            read_ticket_file()
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

    # 4. Shared notes are restricted to the ticket creator, assigned user,
    #    or support lead, for both writing and reading
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

        # Reading shared notes follows the same rule: the creator, the assigned
        # user, and support leads see them, and nobody else does.
        noted_ticket = dict(ticket)
        noted_ticket["notes"] = [
            {
                "id": "N001",
                "author": "Charles",
                "role": "student_fellow",
                "message": "Creator adding details",
                "visibility": "shared",
                "created_at": "2026-10-16T00:00:00+00:00",
            }
        ]

        self.assertEqual(
            get_visible_notes(noted_ticket, creator_user), noted_ticket["notes"]
        )
        self.assertEqual(
            get_visible_notes(noted_ticket, assigned_user), noted_ticket["notes"]
        )
        self.assertEqual(
            get_visible_notes(noted_ticket, lead_user), noted_ticket["notes"]
        )
        self.assertEqual(get_visible_notes(noted_ticket, unrelated_student), [])
        self.assertEqual(get_visible_notes(noted_ticket, unrelated_staff), [])


    # 5. The stored data migrates once to the current format (decision D2)
    def test_migrate_ticket_converts_numeric_string_and_adds_notes(self):
        migrated = migrate_ticket(
            {
                "id": "T001",
                "title": "hello",
                "affected_users": "12",
                "status": "open",
            }
        )

        self.assertEqual(migrated["affected_users"], 12)
        self.assertEqual(migrated["notes"], [])

    def test_migrate_ticket_leaves_other_fields_alone(self):
        original = {
            "id": "T001",
            "assigned_to": "Ada",
            "affected_users": 5,
            "notes": [{"id": "N001"}],
        }

        self.assertEqual(migrate_ticket(original), original)
        self.assertEqual(original["affected_users"], 5)  # not mutated in place

    def test_migrate_ticket_does_not_repair_an_unusable_count(self):
        # A value that is not a whole number is left for the strict loader to
        # reject, rather than being silently guessed at.
        migrated = migrate_ticket({"id": "T001", "affected_users": "3.5"})

        self.assertEqual(migrated["affected_users"], "3.5")

    def test_migrate_tickets_file_writes_a_migrated_store_and_a_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            orig_dir = os.getcwd()
            os.chdir(temp_dir)
            try:
                original = [
                    {"id": "T001", "affected_users": "12", "status": "open"},
                    {"id": "T002", "affected_users": 4, "notes": []},
                ]
                Path("tickets.json").write_text(
                    json.dumps(original), encoding="utf-8"
                )

                count = migrate_tickets_file()

                self.assertEqual(count, 2)
                self.assertEqual(
                    json.loads(Path("tickets.json.bak").read_text(encoding="utf-8")),
                    original,
                )

                # The migrated store loads through the strict loader.
                stored = read_ticket_file()
                self.assertEqual(stored[0]["affected_users"], 12)
                self.assertEqual(stored[0]["notes"], [])
                self.assertEqual(stored[1]["affected_users"], 4)
            finally:
                os.chdir(orig_dir)

    # 6. Resolved tickets reject assignment as well as notes (Requirement A)
    def test_resolved_ticket_rejects_assignment(self):
        from campusflow.assign import assign_ticket

        tickets = [{"id": "T001", "status": "resolved", "assigned_to": None}]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.update_ticket") as update:
                with patch("builtins.input", side_effect=["T001", "Ada"]):
                    with self.assertRaisesRegex(
                        TicketValidationError, "is resolved"
                    ):
                        assign_ticket()

        self.assertIsNone(tickets[0]["assigned_to"])
        update.assert_not_called()

    def test_open_ticket_still_accepts_assignment(self):
        from campusflow.assign import assign_ticket

        tickets = [{"id": "T001", "status": "open", "assigned_to": None}]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch(
                "campusflow.assign.update_ticket", return_value="update success"
            ) as update:
                with patch("builtins.input", side_effect=["T001", "Ada"]):
                    assign_ticket()

        self.assertEqual(tickets[0]["assigned_to"], "Ada")
        update.assert_called_once()


if __name__ == "__main__":
    unittest.main()