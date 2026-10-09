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

    def test_open_cannot_jump_straight_to_resolved(self):
        tickets = [make_ticket("T001", assigned_to="Ada")]
        with self.assertRaises(ValueError):
            change_status(tickets, "T001", "resolved")
        self.assertEqual(tickets[0]["status"], "open")

    def test_resolved_ticket_cannot_change_without_reopen(self):
        tickets = [make_ticket("T001", status="resolved", assigned_to="Ada")]
        with self.assertRaises(ValueError):
            change_status(tickets, "T001", "in_progress")
        self.assertEqual(tickets[0]["status"], "resolved")

    def test_reopen_resolved_ticket_sets_open(self):
        tickets = [make_ticket("T001", status="resolved", assigned_to="Ada")]
        reopen_ticket(tickets, "T001")
        self.assertEqual(tickets[0]["status"], "open")

    def test_reopen_rejected_for_open_ticket(self):
        tickets = [make_ticket("T001")]
        with self.assertRaises(ValueError):
            reopen_ticket(tickets, "T001")
        self.assertEqual(tickets[0]["status"], "open")

    def test_unknown_ticket_id_is_rejected(self):
        tickets = [make_ticket("T001", assigned_to="Ada")]
        with self.assertRaises(ValueError):
            change_status(tickets, "T999", "in_progress")

    def test_invalid_status_is_rejected(self):
        tickets = [make_ticket("T001", assigned_to="Ada")]
        with self.assertRaises(ValueError):
            change_status(tickets, "T001", "finished")
        self.assertEqual(tickets[0]["status"], "open")

    def test_status_input_is_normalised(self):
        tickets = [make_ticket("T001", assigned_to="Ada")]
        change_status(tickets, " t001 ", "In Progress")
        self.assertEqual(tickets[0]["status"], "in_progress")


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

    def test_resolved_tickets_excluded_from_queue(self):
        tickets = [
            make_ticket("T001", priority="critical", status="resolved"),
            make_ticket("T002", priority="low"),
        ]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T002"])

    def test_empty_ticket_list_gives_empty_queue(self):
        self.assertEqual(get_work_queue([]), [])

    def test_queue_does_not_reorder_original_list(self):
        tickets = [
            make_ticket("T001", priority="low"),
            make_ticket("T002", priority="critical"),
        ]
        get_work_queue(tickets)
        self.assertEqual([t["id"] for t in tickets], ["T001", "T002"])


if __name__ == "__main__":
    unittest.main()