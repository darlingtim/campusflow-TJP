"""Tests for the follow-up note menus (Requirement B, milestone B4).

The pure functions are tested directly. The menu functions are tested by
patching input() and print(), and by replacing the file store so the real
note logic in campusflow/notes.py still runs.
"""
import unittest
from unittest.mock import patch

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from campusflow.notes import add_note
from campusflow.notes_menu import (NOTE_MAX_LENGTH, NOTE_MIN_LENGTH,
                                   add_follow_up_note, format_note,
                                   notes_in_id_order, require_noteable,
                                   validate_note_text, view_ticket_notes)
from campusflow.validate_ticket import TicketValidationError

LONG_MESSAGE = "Investigating switch ports"  # 26 characters

STUDENT = {
    "id": "U001",
    "name": "Ada Lovelace",
    "username": "ada",
    "role": "student_fellow",
}
OTHER_STUDENT = {
    "id": "U003",
    "name": "John Doe",
    "username": "john",
    "role": "student_fellow",
}
ASSIGNED_STAFF = {
    "id": "U002",
    "name": "Bob Staff",
    "username": "bob",
    "role": "support_staff",
}
LEAD = {
    "id": "U099",
    "name": "Grace Hopper",
    "username": "grace",
    "role": "support_lead",
}


def make_ticket(ticket_id="T001", status="open", notes=None,
                created_by="U001", assigned_to=None):
    """Build a stored ticket by hand, so we don't depend on the create feature."""
    return {
        "id": ticket_id, "title": "Test", "category": "Other",
        "urgency": "low", "affected_users": 1, "priority": "low",
        "status": status, "assigned_to": assigned_to,
        "created_by": created_by,
        "notes": [] if notes is None else notes,
    }


def make_note(note_id, message="a note", visibility="shared"):
    return {"id": note_id, "author": "Ada", "message": message,
            "visibility": visibility}


class TestValidateNoteText(unittest.TestCase):

    def test_author_must_not_be_blank(self):
        for author in ("", "   "):
            with self.subTest(author=author):
                with self.assertRaises(ValueError):
                    validate_note_text(author, LONG_MESSAGE)

    def test_message_must_not_be_blank(self):
        for message in ("", "   "):
            with self.subTest(message=message):
                with self.assertRaises(ValueError):
                    validate_note_text("Ada", message)

    def test_short_message_is_rejected(self):
        # One character below the minimum.
        with self.assertRaises(ValueError):
            validate_note_text("Ada", "x" * (NOTE_MIN_LENGTH - 1))

    def test_message_at_the_minimum_is_accepted(self):
        author, message = validate_note_text("Ada", "x" * NOTE_MIN_LENGTH)

        self.assertEqual(message, "x" * NOTE_MIN_LENGTH)
        self.assertEqual(author, "Ada")

    def test_message_at_the_maximum_is_accepted(self):
        _, message = validate_note_text("Ada", "x" * NOTE_MAX_LENGTH)

        self.assertEqual(len(message), NOTE_MAX_LENGTH)

    def test_message_over_the_maximum_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_note_text("Ada", "x" * (NOTE_MAX_LENGTH + 1))

    def test_length_is_measured_after_trimming(self):
        # 300 characters of content padded with spaces is still 300.
        padded = "  " + "x" * NOTE_MAX_LENGTH + "  "

        _, message = validate_note_text("Ada", padded)

        self.assertEqual(len(message), NOTE_MAX_LENGTH)

    def test_returned_values_are_trimmed(self):
        author, message = validate_note_text("  Ada  ", "  Investigating  ")

        self.assertEqual(author, "Ada")
        self.assertEqual(message, "Investigating")


class TestNoteableStatus(unittest.TestCase):

    def test_open_and_in_progress_are_accepted(self):
        for status in ("open", "in progress"):
            with self.subTest(status=status):
                ticket = make_ticket(status=status)

                self.assertEqual(require_noteable(ticket), ticket)

    def test_resolved_ticket_is_rejected_with_reopen_guidance(self):
        with self.assertRaises(ValueError) as raised:
            require_noteable(make_ticket(status="resolved"))

        self.assertIn("reopen", str(raised.exception).lower())

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ValueError):
            require_noteable(make_ticket(status="archived"))


class TestNotesInIdOrder(unittest.TestCase):

    def test_notes_are_sorted_numerically_not_as_text(self):
        # As text, "N010" sorts before "N002". As numbers it must not.
        ticket = make_ticket(notes=[make_note("N010"),
                                    make_note("N002"),
                                    make_note("N001")])

        ids = [note["id"] for note in notes_in_id_order(ticket)]

        self.assertEqual(ids, ["N001", "N002", "N010"])

    def test_ticket_without_a_notes_key_gives_an_empty_list(self):
        ticket = make_ticket()
        del ticket["notes"]

        self.assertEqual(notes_in_id_order(ticket), [])

    def test_original_order_is_not_changed(self):
        ticket = make_ticket(notes=[make_note("N002"), make_note("N001")])

        notes_in_id_order(ticket)

        self.assertEqual([n["id"] for n in ticket["notes"]], ["N002", "N001"])

    def test_malformed_note_id_sorts_last(self):
        ticket = make_ticket(notes=[make_note("broken"), make_note("N001")])

        ids = [note["id"] for note in notes_in_id_order(ticket)]

        self.assertEqual(ids, ["N001", "broken"])


class TestFormatNote(unittest.TestCase):

    def test_renders_id_author_and_message(self):
        line = format_note(make_note("N001", "Wi-Fi router reboot attempted"))

        self.assertIn("N001", line)
        self.assertIn("Ada", line)
        self.assertIn("Wi-Fi router reboot attempted", line)

    def test_missing_fields_do_not_crash(self):
        self.assertIsInstance(format_note({}), str)


class TestAddFollowUpNoteMenu(unittest.TestCase):
    """The menu function, driven by patched input()."""

    def _run(self, ticket, answers, user=None):
        user = STUDENT if user is None else user
        with patch("campusflow.notes_menu.read_ticket_file",
                   return_value=[ticket]):
            with patch("campusflow.notes.update_ticket",
                       return_value="update success"):
                with patch("builtins.input", side_effect=answers):
                    with patch("builtins.print"):
                        return add_follow_up_note(user)

    def test_adds_a_note_to_an_open_ticket(self):
        ticket = make_ticket()

        note = self._run(ticket, ["T001", LONG_MESSAGE])

        self.assertEqual(note["id"], "N001")
        self.assertEqual(note["author"], "Ada Lovelace")
        self.assertEqual(note["message"], LONG_MESSAGE)
        self.assertEqual(len(ticket["notes"]), 1)

    def test_adds_a_note_to_an_in_progress_ticket(self):
        ticket = make_ticket(status="in progress")

        note = self._run(ticket, ["T001", LONG_MESSAGE])

        self.assertEqual(note["id"], "N001")

    def test_short_message_is_rejected_and_nothing_is_stored(self):
        ticket = make_ticket()

        note = self._run(ticket, ["T001", "no"])

        self.assertIsNone(note)
        self.assertEqual(ticket["notes"], [])

    def test_note_on_a_resolved_ticket_is_rejected(self):
        ticket = make_ticket(status="resolved")

        note = self._run(ticket, ["T001", LONG_MESSAGE])

        self.assertIsNone(note)
        self.assertEqual(ticket["notes"], [])

    def test_unknown_ticket_id_is_reported(self):
        ticket = make_ticket()

        note = self._run(ticket, ["T999", LONG_MESSAGE])

        self.assertIsNone(note)

    def test_rejected_note_does_not_consume_a_note_id(self):
        # Acceptance case 06. The store already holds N001; a rejected
        # attempt must not push the next valid note to N003.
        ticket = make_ticket(notes=[make_note("N001")])

        rejected = self._run(ticket, ["T001", "no"])
        self.assertIsNone(rejected)

        note = self._run(ticket, ["T001", LONG_MESSAGE])

        self.assertEqual(note["id"], "N002")

    def test_student_who_is_not_on_the_ticket_cannot_add_a_note(self):
        # The login gate supplies an identity, so note permissions can be
        # enforced here instead of trusting whoever reached the menu.
        ticket = make_ticket(created_by="U001")

        note = self._run(ticket, ["T001", LONG_MESSAGE], user=OTHER_STUDENT)

        self.assertIsNone(note)
        self.assertEqual(ticket["notes"], [])

    def test_assigned_staff_choose_visibility(self):
        ticket = make_ticket(assigned_to="U002", created_by="U001")

        note = self._run(
            ticket, ["T001", LONG_MESSAGE, "2"], user=ASSIGNED_STAFF
        )

        self.assertEqual(note["visibility"], "internal")


class TestViewTicketNotesMenu(unittest.TestCase):

    def _run(self, ticket, answers, user=None):
        user = STUDENT if user is None else user
        with patch("campusflow.notes_menu.read_ticket_file",
                   return_value=[ticket]):
            with patch("builtins.input", side_effect=answers):
                with patch("builtins.print") as printed:
                    notes = view_ticket_notes(user)
        lines = [call.args[0] for call in printed.call_args_list if call.args]
        return notes, lines

    def test_prints_notes_in_id_order(self):
        ticket = make_ticket(notes=[make_note("N002", "second"),
                                    make_note("N001", "first")])

        notes, lines = self._run(ticket, ["T001"])

        self.assertEqual([n["id"] for n in notes], ["N001", "N002"])
        note_lines = [line for line in lines if line.startswith("  N")]
        self.assertEqual(note_lines,
                         ["  N001  Ada: first", "  N002  Ada: second"])

    def test_reports_a_ticket_with_no_notes(self):
        ticket = make_ticket()

        notes, lines = self._run(ticket, ["T001"])

        self.assertEqual(notes, [])
        self.assertIn("has no notes yet", " ".join(lines))

    def test_unknown_ticket_id_is_reported(self):
        ticket = make_ticket()

        notes, lines = self._run(ticket, ["T999"])

        self.assertEqual(notes, [])
        self.assertIn("not found", " ".join(lines).lower())

    def test_internal_notes_are_hidden_from_a_student_creator(self):
        ticket = make_ticket(notes=[
            make_note("N001", "shared update"),
            make_note("N002", "internal update", visibility="internal"),
        ])

        notes, _ = self._run(ticket, ["T001"], user=STUDENT)

        self.assertEqual([n["id"] for n in notes], ["N001"])

    def test_support_lead_sees_internal_notes(self):
        ticket = make_ticket(notes=[
            make_note("N001", "shared update"),
            make_note("N002", "internal update", visibility="internal"),
        ])

        notes, _ = self._run(ticket, ["T001"], user=LEAD)

        self.assertEqual([n["id"] for n in notes], ["N001", "N002"])

    def test_user_outside_the_ticket_sees_nothing(self):
        ticket = make_ticket(notes=[make_note("N001")])

        notes, _ = self._run(ticket, ["T001"], user=OTHER_STUDENT)

        self.assertEqual(notes, [])


class TestNoteLifecycleAgainstEngineerACode(unittest.TestCase):
    """The worked example in Requirement B, run against the real note logic.

    Nothing is patched here except the persistence call: this exercises
    campusflow.notes directly, the same API the menu above calls.
    """

    def test_open_add_resolve_reject_reopen_add(self):
        ticket = make_ticket()  # open T001

        with patch("campusflow.notes.update_ticket",
                   return_value="update success"):
            first = add_note(ticket=ticket, user=LEAD,
                             message="Wi-Fi router reboot attempted",
                             visibility="shared")
            second = add_note(ticket=ticket, user=LEAD,
                              message="Investigating switch ports",
                              visibility="shared")

            self.assertEqual([first["id"], second["id"]], ["N001", "N002"])

            ticket["status"] = "resolved"
            with self.assertRaises(TicketValidationError):
                add_note(ticket=ticket, user=LEAD,
                         message="a third note", visibility="shared")

            self.assertEqual(len(ticket["notes"]), 2)  # kept its notes

            ticket["status"] = "open"
            third = add_note(ticket=ticket, user=LEAD,
                             message="Switch port replaced",
                             visibility="shared")

        self.assertEqual(third["id"], "N003")


if __name__ == "__main__":
    unittest.main()
