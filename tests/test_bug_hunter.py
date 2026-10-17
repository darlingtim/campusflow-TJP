"""Bug-hunter tests (sprint section 06).

The brief asks each engineer to devise one previously unlisted edge case for
the other engineer's module, and to record the initial state, the input, the
expected result, the actual result, the test name and any code change made.
That record is in the docstring of the test it belongs to.

This file holds Engineer B's test for Engineer A's module (validation and
ticket creation). Engineer A's test for Engineer B's modules belongs here
too, so both are in one place a reviewer can find.
"""
import unittest
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from campusflow.create_tickets import Ticket
from campusflow.validate_ticket import validate_ticket


class TestAffectedUsersTypeValidation(unittest.TestCase):
    """Engineer B's bug-hunter test, aimed at Engineer A's module."""

    def test_numeric_string_count_is_not_rejected_by_validation(self):
        """A numeric string must not pass validation (Requirement A).

        Initial state : no ticket exists.
        Input         : a Ticket whose affected_users is the string "12".
        Expected      : validate_ticket reports an error. Requirement A says
                        affected_users "must be a strictly positive integer"
                        and to "reject floats, strings and bools masquerading
                        as integers". A string is not an integer.
        Actual when filed: validate_ticket returned no errors. The check was
                        str(value).isdigit(), and "12".isdigit() is True, so
                        the string was accepted. Ticket.calculate_priority
                        then converted it with int() and scored the ticket
                        "high".
        Actual now    : validate_ticket rejects the string. The check requires
                        a real int and excludes bool, and the store is migrated
                        so no ticket is left holding a numeric string.
        Test name     : test_numeric_string_count_is_not_rejected_by_validation
        Code change   : validate_ticket.py now tests isinstance(affected_users,
                        int) and rejects bool and numeric strings;
                        campusflow/migrate.py converts a legacy numeric string
                        on disk; and the strict loader rejects a store that
                        still holds one. The @unittest.expectedFailure
                        decorator this test was filed with has been removed, as
                        the docstring below advised.

        This matters beyond the type check: the repository's own tickets.json
        shipped "affected_users": "12", so the sample data passed only because
        of this hole.
        """
        ticket = Ticket("T900", "Title", "Network", "medium", "12")

        self.assertNotEqual(
            validate_ticket(ticket),
            [],
            "a numeric string is not an integer and must not pass validation",
        )

    def test_boolean_count_is_rejected_by_validation(self):
        # The half of Requirement A that already holds. A bool is not an
        # integer count even though isinstance(True, int) is True.
        ticket = Ticket("T900", "Title", "Network", "medium", True)

        self.assertNotEqual(validate_ticket(ticket), [])

    def test_float_count_is_rejected_by_validation(self):
        ticket = Ticket("T900", "Title", "Network", "medium", 3.9)

        self.assertNotEqual(validate_ticket(ticket), [])

    def test_zero_and_negative_counts_are_rejected_by_validation(self):
        # Requirement A: strictly positive, so zero is as invalid as -5.
        for value in (0, -5):
            with self.subTest(value=value):
                ticket = Ticket("T900", "Title", "Network", "medium", value)

                self.assertNotEqual(validate_ticket(ticket), [])


if __name__ == "__main__":
    unittest.main()
