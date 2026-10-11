
from campusflow.assign_ticket import assign_ticket

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

updated_ticket = assign_ticket(
    tickets,
    "T001",
    "Ada Okafor"
)

print(updated_ticket["assigned_to"])
