from . import load_users, save_users


VALID_ROLES = {
    "student_fellow",
    "support_staff",
    "support_lead",
}

_current_user = None


def get_current_user():
    return _current_user


def register_user():
    users = load_users()

    name = input("Enter your full name: ").strip()
    username = input("Choose a username: ").strip().lower()
    password = input("Choose a password: ").strip()

    if not name or not username or not password:
        raise ValueError("Name, username, and password are required.")

    if any(user["username"] == username for user in users):
        raise ValueError("That username is already registered.")

    # Public registration must not allow users to grant
    # themselves staff or lead permissions.
    role = "student_fellow"

    existing_ids = [
        int(user["id"][1:])
        for user in users
        if isinstance(user.get("id"), str)
        and user["id"].startswith("U")
        and user["id"][1:].isdigit()
    ]
    user = {
        "id": f"U{max(existing_ids, default=0) + 1:03d}",
        "name": name,
        "username": username,
        "password": password,
        "role": role,
    }

    users.append(user)
    save_users(users)

    print("Registration successful. You can now log in.")
    return user


def login_user():
    global _current_user
    users = load_users()

    username = input("Username: ").strip().lower()
    password = input("Password: ").strip()

    for user in users:
        if (
            user["username"] == username
            and user["password"] == password
        ):
            _current_user = user
            print(f"Welcome, {user['name']}!")
            return user

    _current_user = None
    print("Invalid username or password.")
    return None