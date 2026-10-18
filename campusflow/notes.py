from datetime import datetime, timezone

from . import read_ticket_file, update_ticket
from .validate_note import validate_note
from .validate_ticket import TicketValidationError


class Note:
    def __init__(
        self,
        note_id,
        author,
        role,
        message,
        visibility="shared",
        author_id=None,
        created_at=None,
    ):
        self.id = note_id
        self.author = author
        self.role = role
        self.message = message.strip() if isinstance(message, str) else ""
        self.visibility = visibility
        self.author_id = author_id
        self.created_at = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc).isoformat(timespec="seconds")
        )

    def to_dict(self):
        data = {
            "id": self.id,
            "author": self.author,
            "role": self.role,
            "message": self.message,
            "visibility": self.visibility,
            "created_at": self.created_at,
        }
        if self.author_id is not None:
            data["author_id"] = self.author_id
        return data


def _ticket_value(ticket, field):
    if isinstance(ticket, dict):
        return ticket.get(field)
    return getattr(ticket, field, None)


def _ticket_notes(ticket):
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
        if isinstance(note_id, str)
        and note_id.startswith("N")
        and note_id[1:].isdigit()
    ]

    next_number = max(existing_numbers, default=0) + 1
    return f"N{next_number:03d}"


def get_visible_notes(ticket, role):
    """Return only the notes the user's role can view."""
    if isinstance(role, dict):
        role = role.get("role")

    if role not in {
        "student_fellow",
        "support_staff",
        "support_lead",
    }:
        raise PermissionError("Unauthorized user role.")

    notes = _ticket_notes(ticket)

    # Convert Note objects to dicts if needed for read consistency
    dict_notes = [n.to_dict() if hasattr(n, "to_dict") else n for n in notes]

    if role in {"support_staff", "support_lead"}:
        return dict_notes

    return [
        note
        for note in dict_notes
        if _note_value(note, "visibility", "shared") == "shared"
    ]


def _prompt_visibility():
    while True:
        choice = input(
            "Choose note visibility (1 = shared, 2 = internal): "
        ).strip()
        if choice == "1":
            return "shared"
        if choice == "2":
            return "internal"
        print("Invalid visibility. Choose 1 for shared or 2 for internal.")


def add_note(
    ticket=None,
    user=None,
    message=None,
    visibility=None,
):
    """Create a note through the single note-entry workflow."""
    from .auth import get_current_user

    if ticket is None:
        ticket_id = input("Enter ticket ID: ").strip()
        ticket = next(
            (
                stored_ticket
                for stored_ticket in read_ticket_file()
                if stored_ticket.get("id") == ticket_id
            ),
            None,
        )
        if ticket is None:
            raise TicketValidationError(f"Ticket {ticket_id} was not found.")

    if user is None:
        user = get_current_user()
    if user is None:
        raise TicketValidationError("A logged-in user is required.")

    if message is None:
        message = input("Enter note: ")

    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)

    if visibility is None and role in {"support_staff", "support_lead"}:
        visibility = _prompt_visibility()

    validated = validate_note(
        ticket=ticket,
        author=user,
        message=message,
        visibility=visibility,
    )
    if isinstance(validated, list):
        raise TicketValidationError(" ".join(validated))
    return save_note(ticket, validated)


def save_note(ticket, validated):
    """Create a validated note and update its existing ticket."""
    note = Note(
        note_id=generate_note_id(ticket),
        author=validated["author"],
        role=validated["role"],
        message=validated["message"],
        visibility=validated["visibility"],
        author_id=validated.get("author_id"),
    )

    if hasattr(ticket, "add_note"):
        ticket.add_note(note)
        ticket_data = ticket.to_dict()
    else:
        if _ticket_value(ticket, "status") == "resolved":
            raise TicketValidationError("Cannot add notes to a resolved ticket.")
        _ticket_notes(ticket).append(note.to_dict())
        ticket_data = ticket

    result = update_ticket(ticket_data)
    if result != "update success":
        raise TicketValidationError(
            f"Unable to save notes for ticket {_ticket_value(ticket, 'id')}."
        )

    return note.to_dict()