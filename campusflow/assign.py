
from . import read_ticket_file, save_ticket_report

def assign_ticket():
    ticket_id = input("enter ticket ID: ")
    staff_name = input("enter staff name: ")

    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValueError("Staff member name cannot be blank.")

    tickets = read_ticket_file()
    for ticket in tickets:
        if ticket ["id"] == ticket_id:
            ticket ["assigned_to"] = staff_name.strip()
            return save_ticket_report(ticket)

    
