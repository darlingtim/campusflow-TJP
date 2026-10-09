"""Status workflow (F4) and work queue (F5) for CampusFlow.

All functions take the shared list of ticket dictionaries as their first
argument. Invalid actions raise ValueError with a clear message; the CLI
(main.py) is responsible for catching and printing it.
"""

VALID_STATUSES = {"open", "in_progress", "resolved"}

# Which status each status may move to through change_status().
# A resolved ticket can only change through reopen_ticket().
ALLOWED_TRANSITIONS = {
    "open": {"in_progress"},
    "in_progress": {"resolved"},
    "resolved": set(),
}

# Lower number = more urgent = earlier in the queue.
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Team decision: which statuses appear in the work queue.
# Change this one line if the team agrees on "open" only.
QUEUE_STATUSES = {"open", "in_progress"}


def find_ticket(tickets, ticket_id):
    """Return the ticket with this ID, or raise ValueError if not found."""
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("Ticket ID must not be blank.")
    ticket_id = ticket_id.strip().upper()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError(f"Ticket {ticket_id} not found.")


def normalise_status(status):
    """Turn input like ' In Progress ' or 'in-progress' into 'in_progress'."""
    if not isinstance(status, str):
        raise ValueError("Status must be text.")
    return status.strip().lower().replace(" ", "_").replace("-", "_")


def change_status(tickets, ticket_id, new_status):
    """Move a ticket to new_status if the move is allowed. Return the ticket.

    All checks happen BEFORE the ticket is modified, so a rejected
    change never leaves a ticket in a half-updated state.
    """
    ticket = find_ticket(tickets, ticket_id)
    new_status = normalise_status(new_status)

    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{new_status}'. "
            "Choose from: open, in_progress, resolved."
        )

    current = ticket["status"]

    if current == "resolved":
        raise ValueError(
            f"Ticket {ticket['id']} is resolved. Reopen it before changing it."
        )

    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(
            f"Cannot move ticket {ticket['id']} from {current} to {new_status}."
        )

    if new_status == "in_progress":
        assignee = ticket.get("assigned_to")
        if assignee is None or not str(assignee).strip():
            raise ValueError(
                f"Ticket {ticket['id']} must be assigned before it can start."
            )

    ticket["status"] = new_status
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Set a resolved ticket back to open. Return the ticket."""
    ticket = find_ticket(tickets, ticket_id)
    if ticket["status"] != "resolved":
        raise ValueError(
            f"Only resolved tickets can be reopened "
            f"(ticket {ticket['id']} is {ticket['status']})."
        )
    ticket["status"] = "open"
    return ticket


def ticket_number(ticket):
    """Return the numeric part of a ticket ID, e.g. 'T010' -> 10."""
    return int(ticket["id"][1:])


def get_work_queue(tickets):
    """Return a NEW list of unresolved tickets, most urgent first.

    Sorted by priority (critical -> high -> medium -> low), then by the
    numeric ticket ID so earlier tickets win ties. The original list
    is not reordered.
    """
    queue = [t for t in tickets if t["status"] in QUEUE_STATUSES]
    return sorted(
        queue,
        key=lambda t: (PRIORITY_RANK.get(t["priority"], len(PRIORITY_RANK)),
                       ticket_number(t)),
    )