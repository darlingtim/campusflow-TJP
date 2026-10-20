from . import read_ticket_file
from pprint import pprint
def list_tickets(): 
    return pprint(read_ticket_file())


def get_ticket_by_id(ticket_id, tickets=None):
    if not isinstance(ticket_id, str):
        raise ValueError("Invalid ticket ID.")

    for ticket in read_ticket_file() if tickets is None else tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError(f"Ticket {ticket_id} was not found.")


def get_ticket(ticket_id=None):
    if ticket_id is None:
        ticket_id = input("enter ticket ID: ")

    ticket = get_ticket_by_id(ticket_id)
    print("\n")
    pprint(ticket)
    return ticket
