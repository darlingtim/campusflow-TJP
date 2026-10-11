class TicketValidationError(Exception):
    pass

def validate_ticket(ticket):
    errors = []

    if not ticket.title.strip():
        errors.append("Ticket title cannot be empty.")

    if not ticket.category.strip():
        errors.append("Ticket category cannot be empty.")

    if ticket.category.strip().lower() not in ["network", "hardware", "software", "other"]:
        errors.append("Category must be Network, Hardware, Software, or Other.")

    if not ticket.urgency.strip():
            errors.append("Ticket urgency cannot be empty.")

    if ticket.urgency not in ["low", "medium", "high"]:
        errors.append("Urgency must be low, medium, or high.")

    if not ticket.affected_users.strip():
        errors.append("Ticket affected users cannot be empty.")

    if ticket.affected_users.strip().isdigit() == False:
        errors.append("Affected users must be a valid whole number.")

    try:
        if int(ticket.affected_users.strip()) <= 0:
            errors.append("Affected users must be greater than zero.")
    except (ValueError, TypeError):
        errors.append("Affected users must be a valid whole number.")

    return errors