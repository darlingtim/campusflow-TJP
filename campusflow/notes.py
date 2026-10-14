from datetime import datetime, timezone

from . import update_ticket
from .validate_ticket import TicketValidationError


class Note:
    def __init__(self, note_id, author, role, message, visibility="shared"):
        self.id = note_id
        self.author = author
        self.role = role
        self.message = message.strip()
        self.visibility = visibility
        self.created_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "role": self.role,
            "message": self.message,
            "visibility": self.visibility,
            "created_at": self.created_at,
        }


def _ticket_value(ticket, field):
    """Read a ticket field from either a Ticket or stored ticket dictionary."""
    if isinstance(ticket, dict):
        return ticket.get(field)
    return getattr(ticket, field, None)


def _ticket_notes(ticket):
    """Return the ticket's notes, creating the collection when needed."""
    if isinstance(ticket, dict):
        return ticket.setdefault("notes", [])

    if not hasattr(ticket, "notes"):
        ticket.notes = []
    return ticket.notes


def _note_value(note, field, default=None):
    if isinstance(note, dict):
        return note.get(field, default)
    return getattr(note, field, default)


def generate_note_id(ticket):
    """Generate the next note ID for a ticket."""
    existing_numbers = [
        int(note_id[1:])
        for note in _ticket_notes(ticket)
        for note_id in [_note_value(note, "id", "")]
        if note_id.startswith("N") and note_id[1:].isdigit()
    ]

    next_number = max(existing_numbers, default=0) + 1
    return f"N{next_number:03d}"


def add_ticket_note(ticket, author, role, message, visibility="shared"):
    """Add a shared or internal note to a ticket."""

    allowed_roles = {
        "student_fellow",
        "support_staff",
        "support_lead"
    }

    if _ticket_value(ticket, "status") == "resolved":
        raise TicketValidationError(
            "Cannot add notes to a resolved ticket."
        )

    if role not in allowed_roles:
        raise TicketValidationError("Invalid user role.")

    if not isinstance(message, str) or not message.strip():
        raise TicketValidationError("Note cannot be empty.")

    if visibility not in {"shared", "internal"}:
        raise TicketValidationError(
            "Visibility must be shared or internal."
        )

    if visibility == "internal" and role not in {
        "support_staff",
        "support_lead"
    }:
        raise TicketValidationError(
            "Only support staff and support leads "
            "can add internal notes."
        )

    note = Note(
        note_id=generate_note_id(ticket),
        author=author,
        role=role,
        message=message,
        visibility=visibility,
    ).to_dict()

    _ticket_notes(ticket).append(note)

    return note


def get_visible_notes(ticket, role):
    """Return only the notes the user's role can view."""

    if role not in {
        "student_fellow",
        "support_staff",
        "support_lead"
    }:
        raise PermissionError("Unauthorized user role.")

    notes = _ticket_notes(ticket)

    if role in {"support_staff", "support_lead"}:
        return notes.copy()

    return [
        note for note in notes
        if _note_value(note, "visibility", "shared") == "shared"
    ]



def add_and_save_note(ticket, author, role, message, visibility="shared"):
    note = add_ticket_note(
        ticket=ticket,
        author=author,
        role=role,
        message=message,
        visibility=visibility
    )

    ticket_data = ticket if isinstance(ticket, dict) else ticket.to_dict()
    result = update_ticket(ticket_data)
    if result != "update success":
        raise TicketValidationError(
            f"Unable to save notes for ticket {_ticket_value(ticket, 'id')}."
        )

    return note

