"""Interactive command-line interface for campus support tickets."""
from campusflow import raise_ticket, generate_total_ticket_report, assign_ticket, list_tickets, get_ticket, change_status, show_work_queue
def main():
	while True:
		print("\nWelcome to Campusflow-TJP Support")
		print("==========================================")
		print("Please select an option from the menu below:")
		print("\n1. Raise a ticket\n2. List all tickets\n3. Search and view ticket by ID\n4. assign ticket\n5.  view  ticket queue \n6.Update ticket status\n7. Generate ticket report\n8. Exit")
		choice = input("Choose an option: ").strip()

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
			print("You have exited the application.")
			break
		else:
			print("Invalid option.")


if __name__ == "__main__":
	main()
