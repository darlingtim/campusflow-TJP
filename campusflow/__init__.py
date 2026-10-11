import json
import os
from typing import Any, Dict


def save_ticket_report(ticket_data: Dict[str, Any]) -> str:
    """Append a ticket to the existing JSON report."""
    ticket_file = "./tickets.json"
    os.makedirs(os.path.dirname(ticket_file) or ".", exist_ok=True)

    with open(ticket_file, "r") as f:
        existing_data = json.load(f)
        existing_data.append(ticket_data)
    with open(ticket_file, "w") as f:
        json.dump(existing_data, f, indent=4)


def read_ticket_file():
    """Read the ticket report from the JSON file."""
    ticket_file = "./tickets.json"
    if not os.path.exists(ticket_file):
        return []

    with open(ticket_file, "r") as f:
        ticket_data = json.load(f)
    return ticket_data

from . report import generate_total_ticket_report
from . validate_ticket import validate_ticket, TicketValidationError