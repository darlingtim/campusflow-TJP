"""Follow-up note menus (Requirement B, milestone B4).

Engineer B owns the CLI for notes; the note model, its validation and its
persistence belong to Engineer A in campusflow/notes.py. This module only
asks the operator, calls that API, and prints the outcome.

Menu functions (called from main.py) ask for input, load tickets from
tickets.json, run the core logic, save, and print a friendly message.

Core functions take the ticket as an argument and raise ValueError on
invalid input. They never ask for input or touch the file, so they can be
unit-tested without typing (see tests/test_notes_menu.py).
"""

from . import read_ticket_file
from .notes import add_and_save_note
from .validate_ticket import TicketValidationError
from .workflow import find_ticket

# Requirement B: the message is 5-300 characters after trimming.
NOTE_MIN_LENGTH = 5
NOTE_MAX_LENGTH = 300

# Requirement B: only these statuses accept a new note.
NOTEABLE_STATUSES = ("open", "in progress")

# Engineer A's add_ticket_note() requires a role. This application has no
# login, so the CLI does not ask for one and records the operator as
# support staff. Visibility is left at the "shared" default. See
# docs/design-decisions.md D11.
OPERATOR_ROLE = "support_staff"


# ---------------------------------------------------------------------------
# Core logic: no input(), no file access, tested in tests/test_notes_menu.py
# ---------------------------------------------------------------------------

def validate_note_text(author, message):
    """Return (author, message) trimmed, or raise ValueError.

    Requirement B: the author label cannot be blank, and the message must
    be 5-300 characters after trimming. Both checks run before anything is
    written, so a rejected note never reaches the store and never consumes
    a note ID.
    """
    author = (author or "").strip()
    message = (message or "").strip()

    if not author:
        raise ValueError("The author label cannot be blank.")

    if not message:
        raise ValueError("The note message cannot be blank.")

    if not NOTE_MIN_LENGTH <= len(message) <= NOTE_MAX_LENGTH:
        raise ValueError(
            f"The note message must be {NOTE_MIN_LENGTH}-{NOTE_MAX_LENGTH} "
            f"characters after trimming (this one is {len(message)})."
        )

    return author, message


def require_noteable(ticket):
    """Raise ValueError when this ticket's status cannot accept a note."""
    status = ticket.get("status")

    if status == "resolved":
        raise ValueError(
            f"Ticket {ticket.get('id')} is resolved. "
            f"Reopen it before adding a note."
        )

    if status not in NOTEABLE_STATUSES:
        raise ValueError(
            f"Ticket {ticket.get('id')} is '{status}' and cannot accept a note."
        )

    return ticket


def _note_sort_key(note):
    """Sort notes by their number, so N010 follows N002 and not N001.

    A note whose ID is missing or malformed sorts after every numbered
    note rather than breaking the sort.
    """
    note_id = str((note or {}).get("id") or "")

    if note_id.startswith("N") and note_id[1:].isdigit():
        return (0, int(note_id[1:]), note_id)

    return (1, 0, note_id)


def notes_in_id_order(ticket):
    """Return the ticket's notes sorted by note ID, oldest first.

    Returns a new list; the stored order is not changed.
    """
    return sorted(ticket.get("notes") or [], key=_note_sort_key)


def format_note(note):
    """Render one stored note as a display line."""
    note_id = (note or {}).get("id") or "(no id)"
    author = (note or {}).get("author") or "unknown"
    message = (note or {}).get("message") or ""
    return f"  {note_id}  {author}: {message}"


# ---------------------------------------------------------------------------
# Menu functions: called from main.py
# ---------------------------------------------------------------------------

def add_follow_up_note():
    """Menu option: ask for a ticket, author and message, then save a note.

    Errors are printed, never crash the program. A rejected note leaves
    the stored tickets untouched.
    """
    ticket_id = input("Please enter the ticket ID: ")
    author = input("Please enter the author name: ")
    message = input("Please enter the note message: ")

    try:
        ticket = find_ticket(read_ticket_file(), ticket_id)
        author, message = validate_note_text(author, message)
        require_noteable(ticket)
        note = add_and_save_note(
            ticket, author=author, role=OPERATOR_ROLE, message=message
        )
    except (TicketValidationError, ValueError) as error:
        print(f"Error: {error}")
        return None

    print(f"Note {note['id']} added to ticket {ticket['id']}.")
    return note


def view_ticket_notes():
    """Menu option: print every note for a ticket in ID order.

    Every note is shown, including ones marked internal: this CLI has no
    login, so there is no role to filter by. Returns the notes it printed.
    """
    ticket_id = input("Please enter the ticket ID: ")

    try:
        ticket = find_ticket(read_ticket_file(), ticket_id)
    except ValueError as error:
        print(f"Error: {error}")
        return []

    notes = notes_in_id_order(ticket)

    if not notes:
        print(f"Ticket {ticket['id']} has no notes yet.")
        return notes

    print(f"\nNotes for ticket {ticket['id']} ({len(notes)}):")
    for note in notes:
        print(format_note(note))

    return notes
