import json
import os
from pathlib import Path
from typing import Any, Dict, List


def _validate_stored_tickets(records, ticket_file):
    """Reject a stored collection that cannot be trusted.

    Requirement E: an invalid store is rejected as a whole rather than
    partially repaired, so a bad file is never silently reported as empty.
    """
    if not isinstance(records, list):
        raise TicketStorageError(
            f"{ticket_file} does not contain a list of tickets."
        )

    seen_ids = set()
    for record in records:
        if not isinstance(record, dict):
            raise TicketStorageError(
                f"{ticket_file} contains a ticket that is not an object."
            )

        ticket_id = record.get("id")
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise TicketStorageError(
                f"{ticket_file} contains a ticket without a usable id."
            )

        if ticket_id in seen_ids:
            raise TicketStorageError(
                f"{ticket_file} contains the duplicate ticket id {ticket_id}."
            )
        seen_ids.add(ticket_id)


def _load_tickets(ticket_file: str = "./tickets.json") -> List[Dict[str, Any]]:
    """Load tickets, creating an empty store when it does not exist or is empty.

    A corrupt or invalid store raises ``TicketStorageError`` instead of
    loading as empty, so the next save cannot overwrite recoverable data.
    """
    os.makedirs(os.path.dirname(ticket_file) or ".", exist_ok=True)

    if not os.path.exists(ticket_file) or os.path.getsize(ticket_file) == 0:
        with open(ticket_file, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    try:
        with open(ticket_file, "r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as error:
        raise TicketStorageError(
            f"{ticket_file} is not valid JSON, so no tickets were loaded: {error}"
        ) from error

    _validate_stored_tickets(records, ticket_file)
    return records


def save_ticket(ticket_data: Dict[str, Any]) -> str:
    """Save a new ticket or update an existing ticket by ID."""
    ticket_file = "./tickets.json"
    existing_data = _load_tickets(ticket_file)

    for index, ticket in enumerate(existing_data):
        if ticket.get("id") == ticket_data.get("id"):
            existing_data[index] = ticket_data
            break
    else:
        existing_data.append(ticket_data)

    with open(ticket_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4)

    return f"Ticket {ticket_data.get('id')} saved successfully."


def update_ticket(ticket_data: Dict[str, Any]) -> str:
    """Get a ticket by its id and save the updated version."""
    ticket_file = "./tickets.json"
    existing_data = _load_tickets(ticket_file)

    for index, ticket in enumerate(existing_data):
        if ticket.get("id") == ticket_data.get("id"):
            existing_data[index] = ticket_data
            break
    else:
        return "update failed"

    with open(ticket_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4)

    return "update success"


def read_ticket_file() -> List[Dict[str, Any]]:
    """Read the ticket report from the JSON file."""
    return _load_tickets("./tickets.json")


# --- User Storage ---
USERS_FILE = Path("users.json")


def load_users() -> List[Dict[str, Any]]:
    """Load users from the USERS file."""
    if not USERS_FILE.exists() or USERS_FILE.stat().st_size == 0:
        return []

    try:
        with USERS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []


def save_users(users: List[Dict[str, Any]]) -> None:
    """Save users to the USERS file."""
    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


# --- Package Exports ---
# The names below are re-exported for callers such as main.py, so static
# analysis must see them as part of the public API rather than as imports
# that nothing in this module reads.
__all__ = [
    # Storage
    "save_ticket",
    "update_ticket",
    "read_ticket_file",
    "load_users",
    "save_users",
    # Models, validation and notes
    "Ticket",
    "raise_ticket",
    "generate_ticket_id",
    "validate_ticket",
    "TicketStorageError",
    "TicketValidationError",
    "Note",
    "add_note",
    "get_visible_notes",
    "generate_note_id",
    # Ticket operations
    "assign_ticket",
    "list_tickets",
    "get_ticket",
    "change_status",
    "show_work_queue",
    "generate_total_ticket_report",
    # Accounts and menus
    "get_current_user",
    "login_user",
    "register_user",
    "understanding_check_menu",
    "search_tickets_menu",
]

# Core validation and models imported first to prevent circular imports
from .validate_ticket import (
    validate_ticket,
    TicketStorageError,
    TicketValidationError,
)
from .create_tickets import Ticket, raise_ticket, generate_ticket_id
from .notes import Note, add_note, get_visible_notes, generate_note_id
from .assign import assign_ticket
from .list_view import list_tickets, get_ticket
from .workflow import change_status, show_work_queue
from .report import generate_total_ticket_report
from .auth import get_current_user, login_user, register_user
from . understanding_check import understanding_check_menu
from . search import search_tickets_menu