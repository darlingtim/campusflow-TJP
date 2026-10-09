import json
import os

def generate_total_ticket_report():
    """
    Generates a total ticket report and saves it to the specified output file.

    Args:
        output_file (str): The path to the output file where the report will be saved.
    
    # Sample data for demonstration purposes
    ticket_data = {
        "total_tickets": 150,
        "open_tickets": 45,
        "closed_tickets": 105,
        "ticket_details": [
            {"id": 1, "status": "open", "priority": "high"},
            {"id": 2, "status": "closed", "priority": "medium"},
            # Add more ticket details as needed
        ]
    }
    """

    # Ensure the output directory exists
    output_file = "./tickets.json"
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    # Write the report to the specified output file in JSON format
    with open(output_file, 'r') as f:
        ticket_data = json.load(f)

    if len(ticket_data) == 0:
        print("No tickets found in the report.")
        return
    else:
        print(f"Ticket Report Generated.\n---------------------\nTotal tickets:  {len(ticket_data)}\n=======================\nTickets By Status:\n---------------------\nOpen ticket:  {len([ticket for ticket in ticket_data if ticket['status'] == 'open'])}\nTickets in Progress:  {len([ticket for ticket in ticket_data if ticket['status'] == 'in progress'])}\nClosed ticket:  {len([ticket for ticket in ticket_data if ticket['status'] == 'closed'])}\n==============================\nTickets By Priority:\n---------------------\nHigh priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'high'])}\nMedium priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'medium'])}\nLow priority:  {len([ticket for ticket in ticket_data if ticket['priority'] == 'low'])}\n==============================\n")


def save_ticket_report(ticket_data):
    """
    Saves the ticket report to a specified output file in JSON format.

    Args:
        ticket_data (dict): The ticket data to be saved.
        output_file (str): The path to the output file where the report will be saved.
    """
    # Ensure the output directory exists
    output_file = "./tickets.json"
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    # Write the report to the specified output file in JSON format
    with open(output_file, 'r') as f:
        existing_data = json.load(f)
        existing_data.append(ticket_data)
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=4)


generate_total_ticket_report()