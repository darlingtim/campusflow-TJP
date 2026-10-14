import unittest
import sys
from pathlib import Path

if __package__ in (None, ""):
	sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from campusflow.report import generate_total_ticket_report


def make_ticket(ticket_id, status="open", priority="low", category="Network"):
	"""A ticket carrying only the fields the report reads."""
	return {
		"id": ticket_id,
		"title": f"Ticket {ticket_id}",
		"category": category,
		"urgency": "low",
		"affected_users": 1,
		"priority": priority,
		"status": status,
		"assigned_to": None,
	}


class TestTicketsReport(unittest.TestCase):
	def test_generating_a_tickets_report_with_no_tickets_returns_empty_report(self):
		report = generate_total_ticket_report([])

		self.assertEqual(report["total"], 0)
		self.assertEqual(report["tickets"], [])

	def test_empty_report_reports_zero_percent_without_dividing_by_zero(self):
		# Requirement D: an empty dataset must report 0% without errors.
		report = generate_total_ticket_report([])

		self.assertEqual(report["resolution_percent"], 0.0)
		self.assertEqual(report["resolved"], 0)
		self.assertEqual(report["unresolved"], 0)

	def test_generating_a_tickets_report_includes_all_tickets_and_total(self):
		tickets = [
			make_ticket("T001", status="open"),
			make_ticket("T002", status="resolved"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["total"], len(tickets))
		self.assertEqual(report["tickets"], tickets)

	def test_tickets_report_groups_tickets_by_status(self):
		tickets = [
			make_ticket("T001", status="open"),
			make_ticket("T002", status="open"),
			make_ticket("T003", status="in progress"),
			make_ticket("T004", status="resolved"),
		]

		report = generate_total_ticket_report(tickets)

		expected_counts = [("open", 2), ("in progress", 1), ("resolved", 1)]
		for status, expected_count in expected_counts:
			with self.subTest(status=status):
				self.assertEqual(report["by_status"][status], expected_count)

	def test_resolved_tickets_are_counted_in_the_status_breakdown(self):
		# Regression: resolved tickets used to appear in the total and then
		# vanish, because the breakdown only reported open/in progress/closed.
		tickets = [make_ticket("T001", status="resolved")]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["by_status"]["resolved"], 1)
		self.assertEqual(report["total"], 1)

	def test_status_breakdown_has_no_closed_bucket(self):
		# Decision D7: "closed" is not a legal status anywhere in the
		# application, so the report must not claim to count it.
		report = generate_total_ticket_report([make_ticket("T001")])

		self.assertNotIn("closed", report["by_status"])

	def test_status_breakdown_normalises_variant_spellings(self):
		# Decision D4: one canonical spelling. Input variations must land in
		# the same bucket instead of creating lookalike keys.
		tickets = [
			make_ticket("T001", status="in progress"),
			make_ticket("T002", status="In Progress"),
			make_ticket("T003", status="in_progress"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["by_status"]["in progress"], 3)
		self.assertNotIn("in_progress", report["by_status"])

	def test_status_buckets_add_up_to_the_total(self):
		# Requirement D: do not double-count across statuses. If any bucket
		# overlapped another, this sum would exceed the total.
		tickets = [
			make_ticket("T001", status="open"),
			make_ticket("T002", status="in progress"),
			make_ticket("T003", status="resolved"),
			make_ticket("T004", status="open"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(sum(report["by_status"].values()), report["total"])

	def test_reopened_ticket_is_counted_under_its_current_status(self):
		# Requirement D: reopened tickets count according to their CURRENT
		# status. A ticket reopened to open is open, not resolved.
		tickets = [make_ticket("T001", status="open")]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["by_status"]["open"], 1)
		self.assertEqual(report["resolved"], 0)

	def test_tickets_report_counts_unresolved_as_open_plus_in_progress(self):
		tickets = [
			make_ticket("T001", status="open"),
			make_ticket("T002", status="open"),
			make_ticket("T003", status="in progress"),
			make_ticket("T004", status="resolved"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["unresolved"], 3)
		self.assertEqual(report["resolved"], 1)

	def test_tickets_report_calculates_resolution_percentage(self):
		tickets = [
			make_ticket("T001", status="resolved"),
			make_ticket("T002", status="open"),
			make_ticket("T003", status="open"),
			make_ticket("T004", status="open"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["resolution_percent"], 25.0)

	def test_resolution_percentage_rounds_to_one_decimal_place(self):
		tickets = [
			make_ticket("T001", status="resolved"),
			make_ticket("T002", status="open"),
			make_ticket("T003", status="open"),
		]

		report = generate_total_ticket_report(tickets)

		# 1 / 3 * 100 = 33.333... -> 33.3
		self.assertEqual(report["resolution_percent"], 33.3)

	def test_tickets_report_groups_tickets_by_priority(self):
		tickets = [
			make_ticket("T001", priority="critical"),
			make_ticket("T002", priority="critical"),
			make_ticket("T003", priority="medium"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["by_priority"]["critical"], 2)
		self.assertEqual(report["by_priority"]["medium"], 1)
		self.assertEqual(report["by_priority"]["high"], 0)
		self.assertEqual(report["by_priority"]["low"], 0)

	def test_tickets_report_groups_tickets_by_category(self):
		tickets = [
			make_ticket("T001", category="Network"),
			make_ticket("T002", category="Hardware"),
			make_ticket("T003", category="Hardware"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["by_category"]["network"], 1)
		self.assertEqual(report["by_category"]["hardware"], 2)
		self.assertEqual(report["by_category"]["software"], 0)
		self.assertEqual(report["by_category"]["other"], 0)

	def test_category_breakdown_ignores_case(self):
		# create_tickets stores the category exactly as typed, so "Network"
		# and "network" are the same category and must share one bucket.
		tickets = [
			make_ticket("T001", category="Network"),
			make_ticket("T002", category="network"),
			make_ticket("T003", category="NETWORK"),
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["by_category"]["network"], 3)

	def test_tickets_report_does_not_mutate_the_input_collection(self):
		tickets = [make_ticket("T001", status="open")]
		original_tickets = [ticket.copy() for ticket in tickets]

		generate_total_ticket_report(tickets)

		self.assertEqual(tickets, original_tickets)


if __name__ == "__main__":
	unittest.main()
