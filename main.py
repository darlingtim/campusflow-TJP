"""Interactive command-line interface for campus support tickets."""
from campusflow import raise_ticket, generate_total_ticket_report
def main():
	while True:
		print("\nWelcome to Campusflow-TJP Support")
		print("==========================================")
		print("Please select an option from the menu below:")
		print("\n1. Raise a ticket\n2. List all tickets\n3. Search and view ticket by ID\n4. assign ticket\n5. Update ticket status\n6. Generate ticket report\n7. Exit")
		choice = input("Choose an option: ").strip()

		if choice == "1":
			raise_ticket()
		elif choice == "2":
			print("not implemented yet")
		elif choice == "3":
			print("not implemented yet")
		elif choice == "4":
			print("not implemented yet")
		elif choice == "5":
			print("not implemented yet")
		elif choice == "6":
			print("not implemented yet")
		elif choice == "6":
			generate_total_ticket_report()
		elif choice == "7":
			print("You have exited the application.")
			break
		else:
			print("Invalid option.")


if __name__ == "__main__":
	main()
