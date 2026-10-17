"""Interactive command-line interface for campus support tickets."""
from campusflow import (TicketValidationError, assign_ticket, change_status,
						 generate_total_ticket_report, get_ticket, list_tickets,
						 login_user, logout_user, raise_ticket, register_user,
						 show_work_queue, understanding_check_menu,
						 search_tickets_menu)


def report_error(error):
	"""Print an exception in the format the menus use."""
	print("\nError Message:")
	for message in str(error).splitlines():
		print(f"    {message}")


def ticket_menu(user):
	"""Show the ticket menu for a signed-in user until they log out."""
	while True:
		print("\nWelcome to Campusflow-TJP Support")
		print("==========================================")
		print(f"Signed in as {user['name']} ({user['role']})")
		print("Please select an option from the menu below:")
		print("\n1. Raise a ticket\n2. List all tickets\n3. View ticket by ID\n4. assign ticket\n5. view  ticket queue \n6. Update ticket status\n7. Generate ticket report\n8. Search tickets\n9. Engineering Understanding Check\n10. Log out")
		choice = input("\nChoose an option: ").strip()

		try:
			if choice == "1":
				raise_ticket(user)
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
				search_tickets_menu()
			elif choice == "9":
				understanding_check_menu()
			elif choice == "10":
				logout_user()
				return
			else:
				print("\nError:\n    Invalid option. please select a valid option from the menu.")
		except (TicketValidationError, ValueError) as error:
			report_error(error)


def main():
	"""Show the login menu, then the ticket menu for the signed-in user."""
	while True:
		print("\nWelcome to CampusFlow-TJP")
		print("1. Register")
		print("2. Login")
		print("3. Exit")

		choice = input("Choose an option: ").strip()

		try:
			if choice == "1":
				register_user()
			elif choice == "2":
				user = login_user()

				if user is not None:
					ticket_menu(user)
			elif choice == "3":
				print("\nYou have exited the application.")
				return
			else:
				print("Invalid option.")
		except (TicketValidationError, ValueError) as error:
			report_error(error)


if __name__ == "__main__":
	main()
