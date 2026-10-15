from . import read_ticket_file, save_ticket, validate_ticket, TicketValidationError

class Ticket:
    def __init__(self, ticket_id, title, category, urgency, affected_users):
        self.id = ticket_id
        self.title = title
        self.category = category
        self.urgency = urgency
        self.affected_users = affected_users
        self.priority = self.calculate_priority()
        self.status = "open"
        self.assigned_to = None
        self.notes = []

    def calculate_priority(self):
        """Determine the priority of the ticket based on urgency and affected users."""
        try:
            affected_users = int(self.affected_users)
        except (TypeError, ValueError):
            return "low"

        if self.urgency == "high" and affected_users >= 10:
            return "critical"

        elif self.urgency == "high" or affected_users >= 10:
            return "high"

        elif self.urgency == "medium" or affected_users >= 3:
            return "medium"

        else:
            return "low"

    def add_note(self, note):
        """Add a note to the ticket."""
        if self.status == "resolved":
            raise ValueError("Cannot add notes to a resolved ticket.")

        self.notes.append(note)


    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "urgency": self.urgency,
            "affected_users": self.affected_users,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "notes": [
                note.to_dict() if hasattr(note, "to_dict") else note
                for note in self.notes
            ],
        }


def raise_ticket():
    """Function to raise a new ticket."""
    title = input("Enter ticket title: ")
    category = input("Enter category (Network, Hardware, Software, Other): ")
    urgency = input("Enter urgency (low/medium/high): ").lower()
    affected_users = input("Enter number of affected users: ")
    ticket_id =generate_ticket_id()

    ticket = Ticket(
        ticket_id,
        title,
        category,
        urgency,
        affected_users
    )
    
    errors = validate_ticket(ticket)

    if errors:
        raise TicketValidationError("\n".join(errors))
        
    try:
        save_ticket(ticket.to_dict())
        return print(f"\nTicket {ticket.id} has been raised and submitted successfully!")

    except Exception as e:
        return print(f"Error saving ticket: {e}")



def generate_ticket_id():
    """Generate a unique ticket ID for tickets being created."""
    tickets = read_ticket_file()

    if not tickets:
        return "T001"

    last_id = max(int(ticket["id"][1:]) for ticket in tickets)
    return f"T{last_id + 1:03d}"