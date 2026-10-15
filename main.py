"""Interactive command-line interface for campus support tickets."""
from campusflow import (TicketValidationError, add_follow_up_note,
						 assign_ticket, change_status, generate_total_ticket_report,
						 get_ticket, list_tickets, raise_ticket, show_work_queue,
						 view_ticket_notes)


def main():
	while True:
		print("\nWelcome to Campusflow-TJP Support")
		print("==========================================")
		print("Please select an option from the menu below:")
		print("\n1. Raise a ticket\n2. List all tickets\n3. Search and view ticket by ID\n4. assign ticket\n5. view  ticket queue \n6. Update ticket status\n7. Generate ticket report\n8. Add follow-up note\n9. View ticket notes\n10. Exit")
		choice = input("\nChoose an option: ").strip()

		try:
			if choice == "1":
				raise_ticket()
			elif choice == "2":
				list_tickets()
			elif choice == "3":
				get_ticket()
			elif choice == "4":
				assign_ticket()
			elif choice == "5":
				show_work_queue()
			elif choice == "6":
				change_status()
			elif choice == "7":
				generate_total_ticket_report()
			elif choice == "8":
				add_follow_up_note()
			elif choice == "9":
				view_ticket_notes()
			elif choice == "10":
				print("\nYou have exited the application.")
				break
			else:
				print("\nError:\n    Invalid option. please select a valid option from the menu.")
		except (TicketValidationError, ValueError) as error:
			print("\nError Message:")
			for message in str(error).splitlines():
				print(f"    {message}")


if __name__ == "__main__":
	main()
