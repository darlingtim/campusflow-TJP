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

    @unittest.expectedFailure
    def test_numeric_string_count_is_not_rejected_by_validation(self):
        """A numeric string passes validation, contradicting Requirement A.

        Initial state : no ticket exists.
        Input         : a Ticket whose affected_users is the string "12".
        Expected      : validate_ticket reports an error. Requirement A says
                        affected_users "must be a strictly positive integer"
                        and to "reject floats, strings and bools masquerading
                        as integers". A string is not an integer.
        Actual        : validate_ticket returns no errors. The check is
                        str(value).isdigit(), and "12".isdigit() is True, so
                        the string is accepted. Ticket.calculate_priority then
                        converts it with int() and scores the ticket "high".
        Test name     : test_numeric_string_count_is_not_rejected_by_validation
        Code change   : none. The fix belongs in validate_ticket.py, which is
                        Engineer A's module, and must land after the
                        tickets.json migration -- see docs/design-decisions.md
                        D2.

        This matters beyond the type check: the repository's own tickets.json
        ships "affected_users": "12", so today the sample data passes only
        because of this hole. When Engineer A requires an actual int, this
        test starts passing, which unittest reports as an unexpected success.
        Remove the decorator at that point.
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
