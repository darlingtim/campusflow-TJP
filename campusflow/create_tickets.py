from datetime import datetime, timezone

from . import (
    load_users,
    read_ticket_file,
    save_ticket,
    validate_ticket,
    TicketValidationError,
)
from .notes import Note, generate_note_id


class Ticket:
    def __init__(
        self,
        ticket_id,
        title,
        category,
        urgency,
        affected_users,
        created_by=None,
        created_by_name=None,
        initial_note=None,
        creator_role="student_fellow",
        initial_note_visibility="shared",
        assigned_to=None,
        assigned_by=None,
    ):
        self.id = ticket_id
        self.title = title
        self.category = category
        self.urgency = urgency
        self.affected_users = affected_users
        self.priority = self.calculate_priority()
        self.status = "open"
        self.assigned_to = assigned_to
        self.assigned_by = assigned_by
        self.notes = []
        self.created_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
        self.created_by = created_by

        if initial_note is not None and not isinstance(initial_note, str):
            raise TicketValidationError("Initial note must be text.")

        if initial_note is not None and initial_note.strip():
            if not isinstance(created_by, str) or not created_by.strip():
                raise TicketValidationError(
                    "A ticket creator is required for an initial note."
                )

            author_display = (
                created_by_name.strip()
                if isinstance(created_by_name, str) and created_by_name.strip()
                else created_by
            )

            # Store domain Note instance
            self.notes.append(
                Note(
                    note_id=generate_note_id(self),
                    author=author_display,
                    role=creator_role,
                    message=initial_note.strip(),
                    visibility=initial_note_visibility,
                    author_id=created_by,
                )
            )

    def calculate_priority(self):
        """Determine ticket priority based on urgency and affected users."""
        try:
            affected = int(self.affected_users)
        except (TypeError, ValueError):
            return "low"

        if self.urgency == "high" and affected >= 10:
            return "critical"
        elif self.urgency == "high" or affected >= 10:
            return "high"
        elif self.urgency == "medium" or affected >= 3:
            return "medium"
        else:
            return "low"

    def add_note(self, note):
        """Add a note to the ticket."""
        if self.status == "resolved":
            raise TicketValidationError("Cannot add notes to a resolved ticket.")

        self.notes.append(note)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "urgency": self.urgency,
            "affected_users": self.affected_users,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "assigned_by": self.assigned_by,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "notes": [
                note.to_dict() if hasattr(note, "to_dict") else note
                for note in self.notes
            ],
        }


def raise_ticket(current_user=None, initial_note=None):
    """Function to raise a new ticket."""
    title = input("Enter ticket title: ").strip()
    category = input("Enter category (Network, Hardware, Software, Other): ").strip()
    urgency = input("Enter urgency (low/medium/high): ").strip().lower()
    affected_users = input("Enter number of affected users: ").strip()

    created_by = None
    created_by_name = None
    creator_role = "student_fellow"

    if current_user is not None:
        if not isinstance(current_user, dict) or not current_user.get("id"):
            raise TicketValidationError("A valid logged-in user is required.")
        created_by = current_user["id"]
        created_by_name = current_user.get("name") or current_user.get("username")
        creator_role = current_user.get("role", "student_fellow")

    assigned_to = None
    assigned_by = None
    assignment_note = False
    if current_user is not None:
        assignee_name = input(
            "Enter an optional assignee name (press Enter to skip): "
        ).strip()
        if assignee_name:
            allowed_roles = {"support_staff"}
            if creator_role == "support_lead":
                allowed_roles = {"support_staff", "support_lead"}
            target = next((
                user for user in load_users()
                if user.get("role") in allowed_roles
                and assignee_name.casefold() in {
                    str(user.get(field)).strip().casefold()
                    for field in ("id", "name", "username")
                    if user.get(field)
                }
            ), None)
            if target is None:
                raise TicketValidationError(
                    "The selected assignee must have a permitted support role."
                )
            if creator_role == "support_staff" and (
                target.get("id") != current_user.get("id")
            ):
                raise TicketValidationError(
                    "Support staff can only assign an unassigned ticket to themselves."
                )
            assigned_to = target.get("name") or target.get("username")
            assigned_by = created_by_name
            assignment_note = creator_role in {"support_staff", "support_lead"}

    if initial_note is None:
        prompt = (
            "Enter an internal assignment note: "
            if assignment_note
            else "Enter an optional note (press Enter to skip): "
        )
        initial_note = input(prompt).strip()
    initial_note_visibility = "internal" if assignment_note else "shared"

    ticket_id = generate_ticket_id()

    ticket = Ticket(
        ticket_id=ticket_id,
        title=title,
        category=category,
        urgency=urgency,
        affected_users=affected_users,
        created_by=created_by,
        created_by_name=created_by_name,
        initial_note=initial_note if initial_note else None,
        creator_role=creator_role,
        initial_note_visibility=initial_note_visibility,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
    )

    errors = validate_ticket(ticket)
    if errors:
        raise TicketValidationError("\n".join(errors))

    try:
        save_ticket(ticket.to_dict())
        print(f"\nTicket {ticket.id} has been raised and submitted successfully!")
        return ticket
    except Exception as e:
        print(f"Error saving ticket: {e}")
        return None


def generate_ticket_id():
    """Generate a unique ticket ID for tickets being created."""
    tickets = read_ticket_file()

    existing_ids = [
        int(ticket["id"][1:])
        for ticket in tickets
        if isinstance(ticket.get("id"), str)
        and ticket["id"].startswith("T")
        and ticket["id"][1:].isdigit()
    ]

    last_id = max(existing_ids, default=0)
    return f"T{last_id + 1:03d}"