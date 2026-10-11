"""Status workflow (F4) and work queue (F5) for CampusFlow.

Menu functions (called from main.py) ask for input, load tickets from
tickets.json, run the core logic, save, and print a friendly message.

Core functions take the list of tickets as an argument and raise
ValueError on invalid input. They never ask for input or touch the file,
so they can be unit-tested (see tests/test_workflow.py).
"""

from . import read_ticket_file, update_ticket

VALID_STATUSES = {"open", "in progress", "resolved"}

# Which status each status may move to through apply_status_change().
# A resolved ticket can only change through reopen_ticket().
ALLOWED_TRANSITIONS = {
    "open": {"in progress"},
    "in progress": {"resolved"},
    "resolved": set(),
}

# Lower number = more urgent = earlier in the queue.
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Team decision: which statuses appear in the work queue.
QUEUE_STATUSES = {"open", "in progress"}


# ---------------------------------------------------------------------------
# Core logic: no input(), no file access, tested in tests/test_workflow.py
# ---------------------------------------------------------------------------

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
    """Turn input like ' In Progress ' or 'in-progress' into 'in progress'."""
    if not isinstance(status, str):
        raise ValueError("Status must be text.")
    return status.strip().lower().replace("_", " ").replace("-", " ")


def apply_status_change(tickets, ticket_id, new_status):
    """Move a ticket to new_status if the move is allowed. Return the ticket.

    All checks happen BEFORE the ticket is modified, so a rejected
    change never leaves a ticket in a half-updated state.
    """
    ticket = find_ticket(tickets, ticket_id)
    new_status = normalise_status(new_status)

    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{new_status}'. "
            "Choose from: open, in progress, resolved."
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

    if new_status == "in progress":
        assignee = ticket.get("assigned_to")
        if assignee is None or not str(assignee).strip():
            raise ValueError(
                f"Ticket {ticket['id']} must be assigned before status can be change."
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




# ---------------------------------------------------------------------------
# Menu functions: called from main.py
# ---------------------------------------------------------------------------

def change_status():
    """Menu option: ask for a ticket and new status, apply it, and save.

    Entering 'open' for a resolved ticket reopens it (the explicit reopen
    the spec requires). Errors are printed, never crash the program.
    """
    ticket_id = input("Please enter the ticket ID: ")
    new_status = input("Please enter the new status (open, in progress, resolved): ")

    try:
        tickets = read_ticket_file()
        if normalise_status(new_status) == "open":
            ticket = reopen_ticket(tickets, ticket_id)
        else:
            ticket = apply_status_change(tickets, ticket_id, new_status)
    except ValueError as error:
        # Also catches a broken tickets.json (json.JSONDecodeError is a ValueError)
        print(f"Error: {error}")
        return None

    result = update_ticket(ticket)
    if result == "update success":
        print(f"Ticket {ticket['id']} is now {ticket['status']}.")
        return ticket

    print("Error: the status could not be saved.")
    return None

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


def show_work_queue():
    """Menu option: print unresolved tickets in priority order."""
    try:
        queue = get_work_queue(read_ticket_file())
    except ValueError as error:
        print(f"Error: {error}")
        return

    if not queue:
        print("The work queue is empty. No unresolved tickets.")
        return

    print("\nWork queue (most urgent first):")
    for t in queue:
        assignee = t.get("assigned_to") or "unassigned"
        print(f"  {t['id']}  {t['priority']:<8}  {t['status']:<11}  "
              f"{assignee:<12}  {t['title']}")