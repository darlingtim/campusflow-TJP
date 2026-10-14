import json
import os
from typing import Any, Dict


def _load_tickets(ticket_file: str) -> list[Dict[str, Any]]:
    """Load tickets, creating an empty store when it does not exist."""
    os.makedirs(os.path.dirname(ticket_file) or ".", exist_ok=True)

    if not os.path.exists(ticket_file):
        with open(ticket_file, "w") as f:
            json.dump([], f)
        return []

    with open(ticket_file, "r") as f:
        return json.load(f)


def save_ticket(ticket_data: Dict[str, Any]) -> str:
    """Append a ticket to the existing JSON report."""
    ticket_file = "./tickets.json"
    existing_data = _load_tickets(ticket_file)
    existing_data.append(ticket_data)
    with open(ticket_file, "w") as f:
        json.dump(existing_data, f, indent=4)


def update_ticket(ticket_data: Dict[str, Any]) -> str:
    """Gets  a ticket by its id and saves the updated version ."""
    ticket_file = "./tickets.json"
    existing_data = _load_tickets(ticket_file)

    #Update the existing ticket if its ID matches 
    for index, ticket in enumerate(existing_data): 
        if ticket["id"] == ticket_data["id"]: 
            existing_data[index] = ticket_data 
            break
    else:
        return "update failed"

    with open(ticket_file, "w") as f:
            json.dump(existing_data, f, indent=4)
            return "update success"


def read_ticket_file():
    """Read the ticket report from the JSON file."""
    ticket_file = "./tickets.json"
    return _load_tickets(ticket_file)


from .report import generate_total_ticket_report
from .validate_ticket import validate_ticket, TicketValidationError
from .create_tickets import raise_ticket
from .assign import assign_ticket
from .list_view import list_tickets, get_ticket
from .workflow import change_status, show_work_queue
from .notes import (
    add_and_save_note,
    add_ticket_note,
    generate_note_id,
    get_visible_notes,
)
