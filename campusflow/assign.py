
from . import read_ticket_file, update_ticket
from .validate_ticket import TicketValidationError

def assign_ticket():
    ticket_id = input("enter ticket ID: ")
    staff_name = input("enter staff name: ")

    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValueError("Staff member name cannot be blank.")

    tickets = read_ticket_file()
    for ticket in tickets:
        if ticket ["id"] == ticket_id:
            if ticket.get("status") == "resolved":
                raise TicketValidationError(
                    f"Ticket {ticket['id']} is resolved. Reopen it before assigning it."
                )
            ticket ["assigned_to"] = staff_name.strip()
            result = update_ticket(ticket)
            if result == "update success":
                return print(f"\nTicket {ticket["id"]} has been assigned to {ticket["assigned_to"]}.")
            print("\nfailed to assign ticket.")
            return None

    print(f"\nTicket {ticket_id} was not found.")
    return None
