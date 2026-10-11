class TicketValidationError(Exception):
    pass


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

    affected_users_text = str(affected_users).strip() if affected_users is not None else ""
    if not affected_users_text:
        errors.append("Ticket affected users cannot be empty.")

    if not affected_users_text.isdigit():
        errors.append("Affected users must be a valid whole number.")
    elif int(affected_users_text) <= 0:
        errors.append("Affected users must be greater than zero.")

    return errors