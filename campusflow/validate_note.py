from .validate_ticket import TicketValidationError


ALLOWED_NOTE_ROLES = {
    "student_fellow",
    "support_staff",
    "support_lead",
}


def _ticket_value(ticket, field):
    """Read a ticket field from either a Ticket object or dictionary."""
    if isinstance(ticket, dict):
        return ticket.get(field)
    return getattr(ticket, field, None)


def _identity_matches(user_id, user_name, stored_identity):
    """Match a user by ID or name against a stored ticket identity."""
    if isinstance(stored_identity, dict):
        stored_identity = (
            stored_identity.get("id")
            or stored_identity.get("name")
            or stored_identity.get("username")
        )

    if not isinstance(stored_identity, str):
        return False

    stored_target = stored_identity.strip().casefold()

    if user_id and str(user_id).strip().casefold() == stored_target:
        return True

    if not isinstance(user_name, str):
        return False

    user_name_clean = user_name.strip().casefold()
    return (
        user_name_clean == stored_target
        or user_name_clean.split(" ", 1)[0] == stored_target
    )


def validate_note(ticket, author, role=None, message=None, visibility=None):
    """Validate and normalize note input before a note is created."""
    author_id = None

    if isinstance(author, dict):
        if message is None and isinstance(role, str):
            message = role
        role = author.get("role", role)
        author_id = author.get("id")
        author = author.get("name") or author.get("username")

    if _ticket_value(ticket, "status") == "resolved":
        raise TicketValidationError("Cannot add notes to a resolved ticket.")

    if role not in ALLOWED_NOTE_ROLES:
        raise TicketValidationError("Invalid user role.")

    if not isinstance(message, str) or not message.strip():
        raise TicketValidationError("Note cannot be empty.")

    message = message.strip()

    if not isinstance(author, str) or not author.strip():
        raise TicketValidationError("Note owner cannot be blank.")

    # Permissions: Support leads have universal note access.
    # Otherwise, verify ticket creator or assigned user status.
    if role != "support_lead":
        assigned_to = _ticket_value(ticket, "assigned_to")
        created_by = _ticket_value(ticket, "created_by")

        is_assigned = _identity_matches(author_id, author, assigned_to)
        is_ticket_creator = _identity_matches(author_id, author, created_by)

        if not is_assigned and not is_ticket_creator:
            if role == "student_fellow":
                raise TicketValidationError(
                    "Only the ticket creator or assigned staff member can add a note."
                )
            raise TicketValidationError(
                "Only the assigned staff member can add a note."
            )

    if role == "student_fellow":
        visibility = "shared"
    elif visibility is None:
        visibility = "shared"

    if visibility not in {"shared", "internal"}:
        raise TicketValidationError("Visibility must be shared or internal.")

    if visibility == "internal" and role not in {
        "support_staff",
        "support_lead",
    }:
        raise TicketValidationError(
            "Only support staff and support leads can add internal notes."
        )

    return {
        "author": author.strip(),
        "author_id": author_id,
        "role": role,
        "message": message,
        "visibility": visibility,
    }