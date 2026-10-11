
from campusflow.view_tickets import list_tickets, get_ticket

tickets = [
    {
        "id": "T001",
        "title": "Internet is down",
        "category": "Network",
        "urgency": "high",
        "affected_users": 15,
        "priority": "critical",
        "status": "open",
        "assigned_to": None,
    }
]

print(list_tickets(tickets))
print(get_ticket(tickets, "T001"))
