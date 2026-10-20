import unittest
from unittest.mock import patch

from campusflow.assign import assign_ticket


class TestAssignTicket(unittest.TestCase):
    def test_assigns_existing_ticket_and_persists_it(self):
        tickets = [{"id": "T001", "assigned_to": None}]
        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.update_ticket", return_value="update success") as update:
                with patch("builtins.input", side_effect=["T001", "  Ada  "]):
                    result = assign_ticket()

        self.assertIsNone(result)
        self.assertEqual(tickets[0]["assigned_to"], "Ada")
        update.assert_called_once_with(tickets[0])

    def test_blank_staff_name_is_rejected_before_file_access(self):
        with patch("builtins.input", side_effect=["T001", "  "]):
            with self.assertRaises(ValueError):
                assign_ticket()

    def test_unknown_ticket_is_reported(self):
        with patch("campusflow.assign.read_ticket_file", return_value=[]):
            with patch("builtins.input", side_effect=["T999", "Ada"]):
                with patch("builtins.print") as printed:
                    assign_ticket()

        printed.assert_called_once_with("\nTicket T999 was not found.")

    def test_assigned_staff_can_assign_to_another_support_user_with_internal_note(self):
        actor = {
            "id": "U001",
            "name": "Ada",
            "role": "support_staff",
        }
        tickets = [{"id": "T001", "assigned_to": "Ada", "status": "open", "notes": []}]
        users = [
            actor,
            {"id": "U002", "name": "Bea", "role": "support_lead"},
        ]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.load_users", return_value=users):
                with patch("campusflow.assign.update_ticket", return_value="update success"):
                    with patch(
                        "builtins.input",
                        side_effect=["T001", "Bea", "Handing this over"],
                    ):
                        assign_ticket(user=actor)

        self.assertEqual(tickets[0]["assigned_to"], "Bea")
        self.assertEqual(tickets[0]["assigned_by"], "Ada")
        self.assertEqual(tickets[0]["notes"][0]["visibility"], "internal")
        self.assertEqual(tickets[0]["notes"][0]["author"], "Ada")
        self.assertIn("Assigned by: Ada", tickets[0]["notes"][0]["message"])
        self.assertIn("Assigned to: Bea", tickets[0]["notes"][0]["message"])

    def test_staff_cannot_assign_another_staff_members_ticket(self):
        actor = {"id": "U001", "name": "Ada", "role": "support_staff"}
        tickets = [{"id": "T001", "assigned_to": "Bea", "status": "open", "notes": []}]
        users = [actor, {"id": "U002", "name": "Bea", "role": "support_staff"}]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.load_users", return_value=users):
                with patch(
                    "builtins.input",
                    side_effect=["T001", "Bea", "Not allowed"],
                ):
                    with self.assertRaisesRegex(
                        PermissionError,
                        "assigned to them",
                    ):
                        assign_ticket(user=actor)

        self.assertEqual(tickets[0]["assigned_to"], "Bea")
        self.assertEqual(tickets[0]["notes"], [])

    def test_unassigned_staff_can_only_assign_to_themselves(self):
        actor = {"id": "U001", "name": "Ada", "role": "support_staff"}
        tickets = [{"id": "T001", "assigned_to": None, "status": "open", "notes": []}]
        users = [actor, {"id": "U002", "name": "Bea", "role": "support_staff"}]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.load_users", return_value=users):
                with patch(
                    "builtins.input",
                    side_effect=["T001", "Bea", "Not allowed"],
                ):
                    with self.assertRaisesRegex(
                        PermissionError,
                        "only be assigned to yourself",
                    ):
                        assign_ticket(user=actor)

    def test_support_lead_can_assign_themselves_to_any_ticket(self):
        actor = {"id": "U001", "name": "Lead", "role": "support_lead"}
        tickets = [{"id": "T001", "assigned_to": "Bea", "status": "open", "notes": []}]
        users = [
            actor,
            {"id": "U002", "name": "Bea", "role": "support_staff"},
        ]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("campusflow.assign.load_users", return_value=users):
                with patch("campusflow.assign.update_ticket", return_value="update success"):
                    with patch(
                        "builtins.input",
                        side_effect=["T001", "Lead", "Taking ownership"],
                    ):
                        assign_ticket(user=actor)

        self.assertEqual(tickets[0]["assigned_to"], "Lead")

    def test_student_cannot_assign_a_ticket_after_creation(self):
        actor = {"id": "U003", "name": "Student", "role": "student_fellow"}
        tickets = [{"id": "T001", "assigned_to": None, "status": "open", "notes": []}]

        with patch("campusflow.assign.read_ticket_file", return_value=tickets):
            with patch("builtins.input", side_effect=["T001", "Ada"]):
                with self.assertRaisesRegex(
                    PermissionError,
                    "Only support staff and support leads",
                ):
                    assign_ticket(user=actor)

        self.assertIsNone(tickets[0]["assigned_to"])


if __name__ == "__main__":
    unittest.main()
