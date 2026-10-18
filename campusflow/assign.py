
from . import load_users, read_ticket_file, update_ticket
from .auth import get_current_user
from .notes import Note, generate_note_id
from .validate_note import validate_note
from .validate_ticket import TicketValidationError

SUPPORT_ROLES = {"support_staff", "support_lead"}


def _identity_values(user):
    if isinstance(user, dict):
        return {
            str(value).strip().casefold()
            for value in (user.get("id"), user.get("name"), user.get("username"))
            if isinstance(value, str) and value.strip()
        }
    return set()


def _matches_identity(stored_identity, user):
    if isinstance(stored_identity, dict):
        stored_identity = (
            stored_identity.get("id")
            or stored_identity.get("name")
            or stored_identity.get("username")
        )
    return (
        isinstance(stored_identity, str)
        and stored_identity.strip().casefold() in _identity_values(user)
    )


def _display_name(user):
    return user.get("name") or user.get("username") or user.get("id")


def _find_assignee(value, users, allowed_roles=SUPPORT_ROLES):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Staff member name cannot be blank.")

    target = value.strip().casefold()
    for user in users:
        if (
            user.get("role") in allowed_roles
            and target
            in {
                str(user.get(field)).strip().casefold()
                for field in ("id", "name", "username")
                if user.get(field)
            }
        ):
            return user
    raise ValueError("Tickets can only be assigned to support staff or support leads.")


def _validate_assignment_permission(ticket, actor, assignee):
    if not isinstance(actor, dict):
        raise PermissionError("A logged-in user is required to assign tickets.")

    role = actor.get("role")
    if role not in SUPPORT_ROLES:
        raise PermissionError(
            "Only support staff and support leads can assign tickets after creation."
        )

    current_assignee = ticket.get("assigned_to")
    if role == "support_lead":
        if current_assignee and not _matches_identity(current_assignee, actor):
            if not _matches_identity(assignee, actor):
                raise PermissionError(
                    "A support lead may only reassign their own ticket or assign themselves."
                )
    elif current_assignee:
        if not _matches_identity(current_assignee, actor):
            raise PermissionError(
                "Support staff can only assign tickets assigned to them."
            )
    elif not _matches_identity(assignee, actor):
        raise PermissionError(
            "An unassigned ticket can only be assigned to yourself."
        )


def assign_ticket(user=None, assignee=None, note=None):
    """Assign a ticket to one support user and record the required internal note."""
    ticket_id = input("enter ticket ID: ")
    staff_name = assignee if assignee is not None else input("enter staff name: ")

    actor = user if user is not None else get_current_user()
    authenticated = actor is not None
    if actor is None:
        # Preserve the original low-level helper behaviour for callers that
        # have not adopted the authenticated workflow yet.
        actor = {}

    if (
        authenticated
        and note is None
        and isinstance(actor, dict)
        and actor.get("role") in SUPPORT_ROLES
    ):
        note = input("enter internal note: ")

    tickets = read_ticket_file()
    for ticket in tickets:
        if ticket ["id"] == ticket_id:
            if authenticated:
                actor_role = actor.get("role") if isinstance(actor, dict) else None
                if actor_role not in SUPPORT_ROLES:
                    raise PermissionError(
                        "Only support staff and support leads can assign tickets after creation."
                    )
                target = _find_assignee(staff_name, load_users())
                _validate_assignment_permission(ticket, actor, target)
                assigned_to = target.get("name") or target.get("username")
                assignment_message = (
                    f"Assigned by: {_display_name(actor)}\n"
                    f"Assigned to: {assigned_to}\n"
                    f"{note}"
                )
                validated_note = None
                if actor_role in SUPPORT_ROLES:
                    validated_note = validate_note(
                        ticket=ticket,
                        author=actor,
                        message=assignment_message,
                        visibility="internal",
                    )
                    if isinstance(validated_note, list):
                        raise TicketValidationError(" ".join(validated_note))
                ticket["assigned_to"] = assigned_to
                ticket["assigned_by"] = _display_name(actor)
                if validated_note is not None:
                    ticket.setdefault("notes", []).append(
                        Note(
                            note_id=generate_note_id(ticket),
                            author=validated_note["author"],
                            role=validated_note["role"],
                            message=validated_note["message"],
                            visibility="internal",
                            author_id=validated_note.get("author_id"),
                        ).to_dict()
                    )
            else:
                if not isinstance(staff_name, str) or not staff_name.strip():
                    raise ValueError("Staff member name cannot be blank.")
                ticket ["assigned_to"] = staff_name.strip()
                ticket["assigned_by"] = None
            result = update_ticket(ticket)
            if result == "update success":
                return print(f"\nTicket {ticket["id"]} has been assigned to {ticket["assigned_to"]}.")
            print("\nfailed to assign ticket.")
            return None

    print(f"\nTicket {ticket_id} was not found.")
    return None
