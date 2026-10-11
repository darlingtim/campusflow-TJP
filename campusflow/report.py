import json
import os
from . import read_ticket_file as read_ticket


def _build_ticket_report(ticket_data):
    by_status = {}
    for ticket in ticket_data:
        status = ticket["status"].replace(" ", "_")
        by_status[status] = by_status.get(status, 0) + 1

    return {
        "total": len(ticket_data),
        "tickets": ticket_data,
        "by_status": by_status,
    }


def generate_total_ticket_report(ticket_data=None):
    """Generate a ticket report or print the existing JSON report."""
    if ticket_data is not None:
        return _build_ticket_report(ticket_data)

    ticket_data = read_ticket()

    if not ticket_data:
        print("No tickets found in the report.")
        return

    print(
        f"Ticket Report Generated.\n"
        f"---------------------\n"
        f"Total tickets:  {len(ticket_data)}\n"
        f"=======================\n"
        f"Tickets By Status:\n"
        f"---------------------\n"
        f"Open ticket:  {len([ticket for ticket in ticket_data if ticket['status'] == 'open'])}\n"
        f"Tickets in Progress:  {len([ticket for ticket in ticket_data if ticket['status'] in ('in progress', 'in_progress')])}\n"
        f"Closed ticket:  {len([ticket for ticket in ticket_data if ticket['status'] == 'closed'])}\n"
        f"==============================\n"
        f"Tickets By Priority:\n"
        f"------------------------------\n"
        f"Critical priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'critical'])}\n"
        f"High priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'high'])}\n"
        f"Medium priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'medium'])}\n"
        f"Low priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'low'])}\n"
        f"==============================\n"
    )



if __name__ == "__main__":
    generate_total_ticket_report()
