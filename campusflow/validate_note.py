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
    errors = []
    author_id = None

    if isinstance(author, dict):
        if message is None and isinstance(role, str):
            message = role
        role = author.get("role", role)
        author_id = author.get("id")
        author = author.get("name") or author.get("username")

    if _ticket_value(ticket, "status") == "resolved":
        errors.append("Cannot add notes to a resolved ticket.")

    if role not in ALLOWED_NOTE_ROLES:
        errors.append("Invalid user role.")

    if not isinstance(message, str) or not message.strip():
        errors.append("Note cannot be empty.")

    if isinstance(message, str):
        message = message.strip()
        if len(message) < 5 or len(message) > 300:
            errors.append("Note must be between 5 and 300 characters.")

    if not isinstance(author, str) or not author.strip():
        errors.append("Note owner cannot be blank.")

    # Permissions: Support leads have universal note access.
    # Otherwise, verify ticket creator or assigned user status.
    if role != "support_lead":
        assigned_to = _ticket_value(ticket, "assigned_to")
        created_by = _ticket_value(ticket, "created_by")

        is_assigned = _identity_matches(author_id, author, assigned_to)
        is_ticket_creator = _identity_matches(author_id, author, created_by)

        if not is_assigned and not is_ticket_creator:
            if role == "student_fellow":
                errors.append(
                    "Only the ticket creator or assigned staff member can add a note."
                )
            else:
                errors.append("Only the assigned staff member can add a note.")

    if role == "student_fellow":
        visibility = "shared"
    elif visibility is None:
        visibility = "shared"

    if visibility not in {"shared", "internal"}:
        errors.append("Visibility must be shared or internal.")

    if visibility == "internal" and role not in {
        "support_staff",
        "support_lead",
    }:
        errors.append(
            "Only support staff and support leads can add internal notes."
        )

    if errors:
        return errors

    return {
        "author": author.strip(),
        "author_id": author_id,
        "role": role,
        "message": message,
        "visibility": visibility,
    }


def validate_note_view(ticket, user):
    """Return errors when a user is not allowed to view a ticket's notes."""
    user_id = None
    user_name = None

    if isinstance(user, dict):
        role = user.get("role")
        user_id = user.get("id")
        user_name = user.get("name") or user.get("username")
    else:
        role = getattr(user, "role", None)
        user_id = getattr(user, "id", None)
        user_name = getattr(user, "name", None) or getattr(user, "username", None)

    errors = []
    if role not in ALLOWED_NOTE_ROLES:
        return ["Invalid user role."]

    if role == "support_lead":
        return errors

    identity_field = "created_by" if role == "student_fellow" else "assigned_to"
    if not _identity_matches(user_id, user_name, _ticket_value(ticket, identity_field)):
        if role == "student_fellow":
            errors.append("Only the ticket creator can view notes.")
        else:
            errors.append("Only the assigned staff member can view notes.")

    return errors