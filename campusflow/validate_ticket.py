class TicketValidationError(Exception):
    pass


class TicketStorageError(TicketValidationError, ValueError):
    """Raised when stored tickets are corrupt or violate the on-disk format.

    Inherits from ValueError as well so menu functions that catch either
    exception type report the problem instead of crashing.
    """


def validate_ticket(ticket):
    errors = []

    title = ticket.title if isinstance(ticket.title, str) else ""
    category = ticket.category if isinstance(ticket.category, str) else ""
    urgency = ticket.urgency if isinstance(ticket.urgency, str) else ""
    affected_users = ticket.affected_users

    if not title.strip():
        errors.append("Ticket title cannot be empty.")

    if not category.strip():
        errors.append("Ticket category cannot be empty.")

    if category.strip().lower() not in ["network", "hardware", "software", "other"]:
        errors.append("Category must be Network, Hardware, Software, or Other.")

    if not urgency.strip():
        errors.append("Ticket urgency cannot be empty.")

    if urgency.strip().lower() not in ["low", "medium", "high"]:
        errors.append("Urgency must be low, medium, or high.")

    # A real integer only. isinstance(True, int) is True, so bools are checked
    # first, and a numeric string like "12" is not an integer count.
    if isinstance(affected_users, bool) or not isinstance(affected_users, int):
        errors.append("Affected users must be a valid whole number.")
    elif affected_users <= 0:
        errors.append("Affected users must be greater than zero.")

    return errors