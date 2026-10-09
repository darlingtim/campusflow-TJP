import unittest
from campusflow.workflow import change_status, reopen_ticket, get_work_queue


def make_ticket(id, priority="low", status="open", assigned_to=None):
    """Build a test ticket by hand, so we don't depend on the create feature."""
    return {
        "id": id, "title": "Test", "category": "Other", "urgency": "low",
        "affected_users": 1, "priority": priority,
        "status": status, "assigned_to": assigned_to,
    }


class TestWorkflow(unittest.TestCase):

    def test_unassigned_ticket_cannot_start(self):
        tickets = [make_ticket("T001")]
        with self.assertRaises(ValueError):
            change_status(tickets, "T001", "in_progress")
        self.assertEqual(tickets[0]["status"], "open")  # proves nothing changed

    def test_assigned_ticket_full_lifecycle(self):
        tickets = [make_ticket("T001", assigned_to="Ada")]
        change_status(tickets, "T001", "in_progress")
        change_status(tickets, "T001", "resolved")
        self.assertEqual(tickets[0]["status"], "resolved")

    # TODO: resolved ticket can't change without reopen
    # TODO: reopen works on resolved, fails on open
    # TODO: unknown ticket ID raises ValueError


class TestWorkQueue(unittest.TestCase):

    def test_queue_sorted_by_priority_then_id(self):
        tickets = [
            make_ticket("T010", priority="high"),
            make_ticket("T001", priority="low"),
            make_ticket("T002", priority="high"),
            make_ticket("T003", priority="critical"),
        ]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T003", "T002", "T010", "T001"])

    # TODO: resolved tickets excluded
    # TODO: empty list -> []


if __name__ == "__main__":
    unittest.main()