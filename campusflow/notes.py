from datetime import datetime, timezone

from . import read_ticket_file, update_ticket
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


def _identity_matches(user_id, user_name, stored_identity):
    if not isinstance(stored_identity, str):
        return False

    stored_identity = stored_identity.strip().casefold()
    if user_id and str(user_id).strip().casefold() == stored_identity:
        return True
    if not isinstance(user_name, str):
        return False

    user_name = user_name.strip().casefold()
    return (
        user_name == stored_identity
        or user_name.split(" ", 1)[0] == stored_identity
    )


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



def add_ticket_note(ticket, author, role=None, message=None, visibility=None):

    """Add a shared or internal note to a ticket."""

    author_id = None
    if isinstance(author, dict):
        if message is None:
            message = role
        role = author.get("role")
        author_id = author.get("id")
        author = author.get("name") or author.get("username")

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

    if role != "support_lead":
        if not isinstance(author, str) or not author.strip():
            raise TicketValidationError("Note owner cannot be blank.")

        assigned_to = _ticket_value(ticket, "assigned_to")
        created_by = _ticket_value(ticket, "created_by")
        is_assigned_staff = _identity_matches(
            author_id, author, assigned_to
        )
        is_ticket_creator = (
            role == "student_fellow"
            and _identity_matches(author_id, author, created_by)
        )

        if not is_assigned_staff and not is_ticket_creator:
            if role == "student_fellow":
                raise TicketValidationError(
                    "Only the ticket creator or assigned staff member "
                    "can add a note."
                )
            raise TicketValidationError(
                "Only the assigned staff member can add a note."
            )

    if role == "student_fellow":
        visibility = "shared"
    elif visibility is None:
        visibility = _request_visibility()

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
    if author_id is not None:
        note["author_id"] = author_id

    _ticket_notes(ticket).append(note)

    return note


def _request_visibility():
    """Prompt support users to choose shared or internal visibility."""
    while True:
        choice = input(
            "Choose note visibility (1 = shared, 2 = internal): "
        ).strip()
        if choice == "1":
            return "shared"
        if choice == "2":
            return "internal"
        print("Invalid visibility. Choose 1 for shared or 2 for internal.")


def get_visible_notes(ticket, role):
    """Return only the notes the user's role can view."""

    if isinstance(role, dict):
        role = role.get("role")

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


def add_and_save_note(ticket, author, role=None, message=None, visibility=None):

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


def add_note():
    """Prompt for note details for the currently logged-in user."""
    from .auth import get_current_user

    ticket_id = input("Enter ticket ID: ").strip()
    message = input("Enter note: ")
    current_user = get_current_user()
    if current_user is None:
        raise TicketValidationError("A logged-in user is required.")

    tickets = read_ticket_file()
    ticket = next(
        (stored_ticket for stored_ticket in tickets
         if stored_ticket.get("id") == ticket_id),
        None,
    )
    if ticket is None:
        raise TicketValidationError(f"Ticket {ticket_id} was not found.")

    return add_and_save_note(
        ticket=ticket,
        author=current_user,
        message=message,
    )
