import unittest
import sys
from pathlib import Path

if __package__ in (None, ""):
	sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from campusflow.report import generate_total_ticket_report


class TestTicketsReport(unittest.TestCase):
	def test_generating_a_tickets_report_with_no_tickets_returns_empty_report(self):
		report = generate_total_ticket_report([])

		self.assertEqual(report["total"], 0)
		self.assertEqual(report["tickets"], [])

	def test_generating_a_tickets_report_includes_all_tickets_and_total(self):
		tickets = [
			{"id": 1, "title": "Broken projector", "status": "open"},
			{"id": 2, "title": "Missing badge", "status": "closed"},
		]

		report = generate_total_ticket_report(tickets)

		self.assertEqual(report["total"], len(tickets))
		self.assertEqual(report["tickets"], tickets)
	def test_tickets_report_groups_tickets_by_status(self):
		tickets = [
			{"id": 1, "status": "open"},
			{"id": 2, "status": "open"},
			{"id": 3, "status": "in_progress"},
			{"id": 4, "status": "closed"},
		]

		report = generate_total_ticket_report(tickets)

		expected_counts = [("open", 2), ("in_progress", 1), ("closed", 1)]
		for status, expected_count in expected_counts:
			with self.subTest(status=status):
				self.assertEqual(report["by_status"][status], expected_count)


	def test_tickets_report_does_not_mutate_the_input_collection(self):
		tickets = [{"id": 1, "status": "open"}]
		original_tickets = [ticket.copy() for ticket in tickets]

		generate_total_ticket_report(tickets)
		
		self.assertEqual(tickets, original_tickets)


if __name__ == "__main__":
	unittest.main()
