from . import read_ticket_file
from pprint import pprint
def list_tickets(): 
    return pprint(read_ticket_file())


def get_ticket():
    ticket_id = input("enter ticket ID: ")
    if not isinstance(ticket_id, str):
        raise ValueError("Invalid ticket ID.")

    tickets = read_ticket_file()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            print("\n")
            return pprint(ticket)
    raise ValueError(f"Ticket {ticket_id} was not found.")
