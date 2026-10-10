import json
import os


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

    with open("./tickets.json", "r") as f:
        ticket_data = json.load(f)

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
        f"High priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'high'])}\n"
        f"Medium priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'medium'])}\n"
        f"Low priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'low'])}\n"
        f"==============================\n"
    )


def save_ticket_report(ticket_data):
    """Append a ticket to the existing JSON report."""
    output_file = "./tickets.json"
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    with open(output_file, "r") as f:
        existing_data = json.load(f)
        existing_data.append(ticket_data)
    with open(output_file, "w") as f:
        json.dump(existing_data, f, indent=4)


if __name__ == "__main__":
    generate_total_ticket_report()
