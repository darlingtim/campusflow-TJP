import json
import os
import tempfile
import unittest
from unittest.mock import patch

from campusflow.create_tickets import Ticket
from campusflow.notes import (
    Note,
    add_note,
    generate_note_id,
    get_visible_notes,
    view_notes,
)
from campusflow.validate_note import validate_note, validate_note_view
from campusflow.validate_ticket import TicketValidationError


def add_ticket_note(ticket, author, role=None, message=None, visibility=None):
    user = author if isinstance(author, dict) else {
        "name": author,
        "role": role,
    }
    if isinstance(author, dict) and message is None:
        message = role
    with patch("campusflow.notes.update_ticket", return_value="update success"):
        return add_note(
            ticket=ticket,
            user=user,
            message=message,
            visibility=visibility,
        )


def make_ticket(status="open"):
    ticket = Ticket("T001", "Wi-Fi outage", "Network", "high", "3")
    ticket.status = status
    ticket.assigned_to = "Ada"
    return ticket


class TestNote(unittest.TestCase):
    def test_validate_note_normalizes_authenticated_user(self):
        ticket = make_ticket()
        user = {
            "id": "U001",
            "name": "Ada",
            "role": "support_staff",
        }

        with patch("builtins.input", return_value="1"):
            validated = validate_note(ticket, user, "Update")

        self.assertEqual(
            validated,
            {
                "author": "Ada",
                "author_id": "U001",
                "role": "support_staff",
                "message": "Update",
                "visibility": "shared",
            },
        )

    def test_validate_note_returns_all_validation_errors(self):
        errors = validate_note(
            make_ticket("resolved"),
            {"name": "Bea", "role": "guest"},
            message="",
            visibility="private",
        )

        self.assertEqual(
            errors,
            [
                "Cannot add notes to a resolved ticket.",
                "Invalid user role.",
                "Note cannot be empty.",
                "Note must be between 5 and 300 characters.",
                "Only the assigned staff member can add a note.",
                "Visibility must be shared or internal.",
            ],
        )

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
                ticket.assigned_to = "Ada"
                if role == "student_fellow":
                    note = add_ticket_note(ticket, "Ada", role, "  Update  ")
                else:
                    with patch("builtins.input", return_value="1"):
                        note = add_ticket_note(ticket, "Ada", role, "  Update  ")

                self.assertEqual(note["id"], "N001")
                self.assertEqual(note["message"], "Update")
                self.assertEqual(note["visibility"], "shared")
                self.assertEqual(ticket.to_dict()["notes"], [note])

    def test_authenticated_user_can_add_note_and_note_keeps_user_id(self):
        ticket = make_ticket()
        user = {
            "id": "U001",
            "name": "Ada Lovelace",
            "role": "support_staff",
        }

        with patch("builtins.input", return_value="1"):
            note = add_ticket_note(ticket, user, "Investigating")

        self.assertEqual(note["author"], "Ada Lovelace")
        self.assertEqual(note["author_id"], "U001")
        self.assertEqual(note["role"], "support_staff")

    def test_non_lead_note_owner_must_be_assigned_to_ticket(self):
        for assigned_to, author in ((None, "Ada"), ("Bea", "Ada")):
            with self.subTest(assigned_to=assigned_to, author=author):
                ticket = make_ticket()
                ticket.assigned_to = assigned_to

                with self.assertRaisesRegex(
                    TicketValidationError,
                    "Only the assigned staff member can add a note.",
                ):
                    with patch("builtins.input", return_value="1"):
                        add_ticket_note(
                            ticket,
                            author,
                            "support_staff",
                            "Update",
                        )

                self.assertEqual(ticket.notes, [])

    def test_added_note_cannot_be_empty(self):
        ticket = make_ticket()

        with self.assertRaisesRegex(
            TicketValidationError,
            "Note cannot be empty.",
        ):
            add_ticket_note(
                ticket,
                "Ada",
                "support_staff",
                "  ",
                visibility="shared",
            )

        self.assertEqual(ticket.notes, [])

    def test_support_lead_can_add_note_to_unassigned_ticket(self):
        ticket = make_ticket()

        with patch("builtins.input", return_value="1"):
            note = add_ticket_note(ticket, "Lead", "support_lead", "Update")

        self.assertEqual(ticket.to_dict()["notes"], [note])

    def test_support_note_prompts_for_internal_visibility(self):
        ticket = make_ticket()

        with patch("builtins.input", side_effect=["invalid", "2"]):
            note = add_ticket_note(ticket, "Ada", "support_staff", "Internal update")

        self.assertEqual(note["visibility"], "internal")

    def test_student_fellow_can_add_note_to_ticket_they_created(self):
        ticket = make_ticket()
        ticket.assigned_to = None
        ticket.created_by = "Ada"

        note = add_ticket_note(ticket, "Ada", "student_fellow", "More details")

        self.assertEqual(ticket.to_dict()["notes"], [note])

    def test_student_fellow_cannot_add_note_to_ticket_created_by_someone_else(self):
        ticket = make_ticket()
        ticket.assigned_to = None
        ticket.created_by = "Bea"

        with self.assertRaisesRegex(
            TicketValidationError,
            "Only the ticket creator or assigned staff member can add a note.",
        ):
            add_ticket_note(ticket, "Ada", "student_fellow", "More details")

        self.assertEqual(ticket.notes, [])

    def test_student_fellow_note_visibility_is_always_shared(self):
        ticket = make_ticket()

        note = add_ticket_note(
            ticket,
            "Ada",
            "student_fellow",
            "Student update",
            visibility="internal",
        )

        self.assertEqual(note["visibility"], "shared")

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
        with patch("builtins.input", return_value="1"):
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

    def test_view_notes_validates_ticket_access_and_note_visibility(self):
        ticket = {
            "id": "T001",
            "status": "open",
            "created_by": "U001",
            "assigned_to": "U002",
            "notes": [
                {"id": "N001", "visibility": "shared", "message": "Shared"},
                {"id": "N002", "visibility": "internal", "message": "Internal"},
            ],
        }
        student = {"id": "U001", "name": "Ada", "role": "student_fellow"}
        staff = {"id": "U002", "name": "Bea", "role": "support_staff"}
        lead = {"id": "U003", "name": "Cal", "role": "support_lead"}
        stranger = {"id": "U004", "name": "Dan", "role": "student_fellow"}

        self.assertEqual(len(view_notes(ticket, student)), 1)
        self.assertEqual(len(view_notes(ticket, staff)), 2)
        self.assertEqual(len(view_notes(ticket, lead)), 2)
        self.assertEqual(
            validate_note_view(ticket, stranger),
            ["Only the ticket creator can view notes."],
        )
        with self.assertRaisesRegex(
            PermissionError,
            "Only the ticket creator can view notes.",
        ):
            view_notes(ticket, stranger)

    def test_view_notes_loads_ticket_and_current_user(self):
        ticket = {
            "id": "T001",
            "status": "open",
            "created_by": "U001",
            "notes": [
                {"id": "N001", "visibility": "shared", "message": "Shared"},
                {"id": "N002", "visibility": "internal", "message": "Internal"},
            ],
        }

        with patch("campusflow.notes.get_ticket_by_id", return_value=ticket):
            with patch(
                "campusflow.notes.require_current_user",
                return_value={
                    "id": "U001",
                    "name": "Ada",
                    "role": "student_fellow",
                },
            ):
                self.assertEqual(view_notes("T001"), [ticket["notes"][0]])

    def test_view_notes_prompts_for_ticket_when_not_provided(self):
        ticket = {
            "id": "T001",
            "status": "open",
            "created_by": "U001",
            "notes": [
                {"id": "N001", "visibility": "shared", "message": "Shared"},
            ],
        }

        with patch("campusflow.notes.get_ticket_by_id", return_value=ticket):
            with patch("builtins.input", return_value="T001"):
                with patch("campusflow.notes.pprint") as printed_notes:
                    with patch(
                        "campusflow.notes.require_current_user",
                        return_value={
                            "id": "U001",
                            "name": "Ada",
                            "role": "student_fellow",
                        },
                    ):
                        result = view_notes()
                        self.assertEqual(result, [ticket["notes"][0]])
                        printed_notes.assert_called_once_with([ticket["notes"][0]])

    def test_dictionary_ticket_is_supported_and_missing_notes_are_initialized(self):
        ticket = {"id": "T001", "status": "open"}

        note = add_ticket_note(
            ticket,
            "Ada",
            "support_lead",
            "Update",
            visibility="shared",
        )

        self.assertEqual(ticket["notes"], [note])
        self.assertEqual(get_visible_notes(ticket, "support_lead"), [note])

    def test_save_note_persists_note_added_to_ticket_object(self):
        ticket = make_ticket()

        with tempfile.TemporaryDirectory() as directory:
            old_directory = os.getcwd()
            os.chdir(directory)
            try:
                with open("tickets.json", "w") as tickets_file:
                    json.dump([ticket.to_dict()], tickets_file)

                with patch("builtins.input", return_value="1"):
                    note = add_note(
                        ticket=ticket,
                        user={"name": "Ada", "role": "support_staff"},
                        message="Persisted object update",
                    )

                with open("tickets.json") as tickets_file:
                    stored_tickets = json.load(tickets_file)
            finally:
                os.chdir(old_directory)

        self.assertEqual(ticket.to_dict()["notes"], [note])
        self.assertEqual(len(stored_tickets), 1)
        self.assertEqual(stored_tickets[0]["notes"], [note])

    def test_add_note_appends_note_to_ticket(self):
        ticket = make_ticket()
        note = Note("N001", "Ada", "support_staff", "Direct update")

        ticket.add_note(note)

        self.assertEqual(ticket.notes, [note])
        self.assertEqual(ticket.to_dict()["notes"], [note.to_dict()])

    def test_add_note_rejects_resolved_ticket(self):
        ticket = make_ticket(status="resolved")
        note = Note("N001", "Ada", "support_staff", "Direct update")

        with self.assertRaisesRegex(
            TicketValidationError,
            "Cannot add notes to a resolved ticket.",
        ):
            ticket.add_note(note)

        self.assertEqual(ticket.notes, [])

    def test_save_note_updates_existing_ticket_without_appending_duplicate(self):
        ticket_data = make_ticket().to_dict()

        with tempfile.TemporaryDirectory() as directory:
            old_directory = os.getcwd()
            os.chdir(directory)
            try:
                with open("tickets.json", "w") as tickets_file:
                    json.dump([ticket_data], tickets_file)

                with patch("builtins.input", return_value="1"):
                    note = add_note(
                        ticket=ticket_data,
                        user={"name": "Ada", "role": "support_staff"},
                        message="Persisted update",
                    )

                with open("tickets.json") as tickets_file:
                    stored_tickets = json.load(tickets_file)
            finally:
                os.chdir(old_directory)

        self.assertEqual(len(stored_tickets), 1)
        self.assertEqual(stored_tickets[0]["notes"], [note])

    def test_save_note_reports_persistence_failure(self):
        ticket = make_ticket()

        with patch("campusflow.notes.update_ticket", return_value="update failed"):
            with self.assertRaisesRegex(
                TicketValidationError,
                "Unable to save notes for ticket T001.",
            ):
                add_note(
                    ticket=ticket,
                    user={"name": "Ada", "role": "support_staff"},
                    message="Update",
                    visibility="shared",
                )

    def test_add_note_prompts_for_details_and_saves_selected_ticket(self):
        ticket = make_ticket()

        with patch("campusflow.notes.read_ticket_file", return_value=[ticket.to_dict()]):
            with patch("campusflow.auth.get_current_user", return_value={
                "id": "U001",
                "name": "Ada",
                "role": "support_staff",
            }):
                with patch("builtins.input", side_effect=["T001", "1", "Update"]):
                    with patch(
                        "campusflow.notes.update_ticket",
                        return_value="update success",
                    ):
                        note = add_note()

        self.assertEqual(note["message"], "Update")
        self.assertEqual(note["visibility"], "shared")


if __name__ == "__main__":
    unittest.main()
