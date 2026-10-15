"""Tests for read-only search and priority sorting (Requirement C and D)."""
import unittest

from campusflow.search import search_tickets, sort_by_priority


def make_ticket(ticket_id, title="Test", category="Other", priority="low",
                status="open", assigned_to=None):
    """Build a ticket by hand so the tests do not depend on the create feature."""
    return {
        "id": ticket_id, "title": title, "category": category,
        "urgency": "low", "affected_users": 1, "priority": priority,
        "status": status, "assigned_to": assigned_to,
    }


class TestSearchTickets(unittest.TestCase):

    def setUp(self):
        self.tickets = [
            make_ticket("T001", "Wi-Fi router reboot", "Network", "high", "open"),
            make_ticket("T002", "Wi-Fi outage in library", "Network",
                        "critical", "in progress", "Ada"),
            make_ticket("T003", "Laptop battery swollen", "Hardware",
                        "medium", "resolved", "Ada"),
            make_ticket("T004", "Email client crash", "Software", "low", "open"),
        ]

    def test_title_match_ignores_case_and_matches_substring(self):
        expected = {
            "wi-fi": ["T001", "T002"],
            "WI-FI": ["T001", "T002"],
            "Wi-Fi": ["T001", "T002"],
            "router": ["T001"],
            "battery swollen": ["T003"],
        }
        for query, ids in expected.items():
            with self.subTest(query=query):
                self.assertEqual(
                    [t["id"] for t in search_tickets(self.tickets, title=query)],
                    ids,
                )

    def test_all_supplied_filters_must_match(self):
        ids = [t["id"] for t in search_tickets(
            self.tickets, title="wi-fi", category="Network", status="open")]
        self.assertEqual(ids, ["T001"])

    def test_a_mismatched_filter_excludes_the_ticket(self):
        # T001 matches the title but is not a Hardware ticket.
        self.assertEqual(
            search_tickets(self.tickets, title="wi-fi", category="Hardware"), [])

    def test_blank_filters_do_not_filter_anything(self):
        for blank in (None, "", "   "):
            with self.subTest(blank=repr(blank)):
                self.assertEqual(
                    search_tickets(self.tickets, title=blank, category=blank,
                                   status=blank, priority=blank),
                    self.tickets,
                )

    def test_status_filter_accepts_separator_and_case_variants(self):
        for value in ("in progress", "In Progress", "in_progress", "IN-PROGRESS"):
            with self.subTest(value=value):
                self.assertEqual(
                    [t["id"] for t in search_tickets(self.tickets, status=value)],
                    ["T002"],
                )

    def test_priority_and_category_filters_ignore_case(self):
        self.assertEqual(
            [t["id"] for t in search_tickets(self.tickets, priority="CRITICAL")],
            ["T002"],
        )
        self.assertEqual(
            [t["id"] for t in search_tickets(self.tickets, category="software")],
            ["T004"],
        )

    def test_no_match_returns_an_empty_list(self):
        self.assertEqual(search_tickets(self.tickets, title="printer"), [])

    def test_search_does_not_modify_the_collection(self):
        original = [dict(ticket) for ticket in self.tickets]
        search_tickets(self.tickets, title="wi-fi", status="open")
        self.assertEqual(self.tickets, original)

    def test_search_returns_a_new_list(self):
        results = search_tickets(self.tickets, title="wi-fi")
        self.assertIsNot(results, self.tickets)
        results.clear()
        self.assertEqual(len(self.tickets), 4)

    def test_search_preserves_input_order(self):
        ids = [t["id"] for t in search_tickets(self.tickets)]
        self.assertEqual(ids, ["T001", "T002", "T003", "T004"])


class TestSortByPriority(unittest.TestCase):

    def test_orders_by_priority_then_ticket_number(self):
        tickets = [
            make_ticket("T010", priority="high"),
            make_ticket("T001", priority="low"),
            make_ticket("T002", priority="high"),
            make_ticket("T003", priority="critical"),
        ]
        self.assertEqual(
            [t["id"] for t in sort_by_priority(tickets)],
            ["T003", "T002", "T010", "T001"],
        )

    def test_tie_break_is_numeric_not_string_order(self):
        # Sorted as text, "T1000" would come before "T999".
        tickets = [
            make_ticket("T1000", priority="high"),
            make_ticket("T999", priority="high"),
        ]
        self.assertEqual(
            [t["id"] for t in sort_by_priority(tickets)],
            ["T999", "T1000"],
        )

    def test_sort_does_not_reorder_the_input(self):
        tickets = [
            make_ticket("T001", priority="low"),
            make_ticket("T002", priority="critical"),
        ]
        sort_by_priority(tickets)
        self.assertEqual([t["id"] for t in tickets], ["T001", "T002"])


if __name__ == "__main__":
    unittest.main()
