import json
import os
import tempfile
import unittest
from unittest.mock import patch

from campusflow.create_tickets import Ticket
from campusflow.notes import (
    Note,
    add_and_save_note,
    add_ticket_note,
    generate_note_id,
    get_visible_notes,
)
from campusflow.validate_ticket import TicketValidationError


def make_ticket(status="open"):
    ticket = Ticket("T001", "Wi-Fi outage", "Network", "high", "3")
    ticket.status = status
    return ticket


class TestNote(unittest.TestCase):
    def test_note_strips_message_and_serializes_all_fields(self):
        note = Note("N001", "Ada", "support_staff", "  Investigating  ", "internal")

        self.assertEqual(
            note.to_dict() | {"created_at": note.created_at},
            {
                "id": "N001",
                "author": "Ada",
                "role": "support_staff",
                "message": "Investigating",
                "visibility": "internal",
                "created_at": note.created_at,
            },
        )

    def test_generate_note_id_uses_highest_valid_existing_id(self):
        ticket = {
            "id": "T001",
            "status": "open",
            "notes": [
                {"id": "N002"},
                {"id": "N010"},
                {"id": "bad"},
                {"id": "Nnot-a-number"},
            ],
        }

        self.assertEqual(generate_note_id(ticket), "N011")

    def test_add_shared_note_accepts_all_allowed_roles(self):
        for role in ("student_fellow", "support_staff", "support_lead"):
            with self.subTest(role=role):
                ticket = make_ticket()
                note = add_ticket_note(ticket, "Ada", role, "  Update  ")

                self.assertEqual(note["id"], "N001")
                self.assertEqual(note["message"], "Update")
                self.assertEqual(note["visibility"], "shared")
                self.assertEqual(ticket.notes, [note])

    def test_add_internal_note_requires_support_role(self):
        with self.assertRaisesRegex(
            TicketValidationError,
            "Only support staff and support leads can add internal notes.",
        ):
            add_ticket_note(
                make_ticket(),
                "Student",
                "student_fellow",
                "Staff-only update",
                visibility="internal",
            )

    def test_add_note_rejects_invalid_role_message_visibility_and_resolved_ticket(self):
        cases = [
            ("Invalid user role.", ("Ada", "guest", "Message", "shared")),
            ("Note cannot be empty.", ("Ada", "support_staff", "  ", "shared")),
            (
                "Visibility must be shared or internal.",
                ("Ada", "support_staff", "Message", "private"),
            ),
            (
                "Cannot add notes to a resolved ticket.",
                ("Ada", "support_staff", "Message", "shared"),
            ),
        ]

        for expected_error, arguments in cases:
            with self.subTest(message=expected_error):
                ticket = make_ticket(
                    "resolved"
                    if expected_error == "Cannot add notes to a resolved ticket."
                    else "open"
                )
                with self.assertRaisesRegex(TicketValidationError, expected_error):
                    add_ticket_note(ticket, *arguments)
                self.assertEqual(ticket.notes, [])

    def test_get_visible_notes_hides_internal_notes_from_student(self):
        ticket = make_ticket()
        shared = add_ticket_note(ticket, "Ada", "support_staff", "Shared update")
        internal = add_ticket_note(
            ticket,
            "Ada",
            "support_staff",
            "Internal update",
            visibility="internal",
        )

        self.assertEqual(get_visible_notes(ticket, "student_fellow"), [shared])
        self.assertEqual(
            get_visible_notes(ticket, "support_staff"),
            [shared, internal],
        )

    def test_get_visible_notes_rejects_unknown_role(self):
        with self.assertRaisesRegex(PermissionError, "Unauthorized user role."):
            get_visible_notes(make_ticket(), "guest")

    def test_dictionary_ticket_is_supported_and_missing_notes_are_initialized(self):
        ticket = {"id": "T001", "status": "open"}

        note = add_ticket_note(ticket, "Ada", "support_lead", "Update")

        self.assertEqual(ticket["notes"], [note])
        self.assertEqual(get_visible_notes(ticket, "support_lead"), [note])

    def test_add_and_save_note_updates_existing_ticket_without_appending_duplicate(self):
        ticket_data = make_ticket().to_dict()

        with tempfile.TemporaryDirectory() as directory:
            old_directory = os.getcwd()
            os.chdir(directory)
            try:
                with open("tickets.json", "w") as tickets_file:
                    json.dump([ticket_data], tickets_file)

                note = add_and_save_note(
                    ticket_data,
                    "Ada",
                    "support_staff",
                    "Persisted update",
                )

                with open("tickets.json") as tickets_file:
                    stored_tickets = json.load(tickets_file)
            finally:
                os.chdir(old_directory)

        self.assertEqual(len(stored_tickets), 1)
        self.assertEqual(stored_tickets[0]["notes"], [note])

    def test_add_and_save_note_reports_persistence_failure(self):
        ticket = make_ticket()

        with patch("campusflow.notes.update_ticket", return_value="update failed"):
            with self.assertRaisesRegex(
                TicketValidationError,
                "Unable to save notes for ticket T001.",
            ):
                add_and_save_note(ticket, "Ada", "support_staff", "Update")


if __name__ == "__main__":
    unittest.main()
