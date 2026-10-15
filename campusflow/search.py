

"""Read-only ticket search (Requirement C) for CampusFlow.

This module follows the same two-layer pattern as ``workflow.py``:

* ``search_tickets`` and ``sort_by_priority`` are **pure**. They take a list of
  ticket dictionaries and return a new list. They never ask for input, never
  touch the file, and never modify the tickets they are given, so they can be
  tested directly (see ``tests/test_search.py``).
* ``search_tickets_menu`` is the CLI view called from ``main.py``. It collects
  the filters, loads the tickets, and prints a table.

A ticket is a plain dictionary. The keys used here are ``id``, ``title``,
``category``, ``priority``, ``status`` and ``assigned_to``.
"""

from . import read_ticket_file
from .workflow import PRIORITY_RANK, VALID_STATUSES, normalise_status, ticket_number

# Accepted filter values. The brief requires invalid filter options to
# re-prompt, so these sets drive validation as well as the help text.
#
# TODO(contract): the category and priority lists are duplicated from
# ``validate_ticket``. They should live in one shared module owned by
# Engineer A so the two engineers cannot drift apart. See docs/design-decisions.md.
CATEGORIES = frozenset({"network", "hardware", "software", "other"})
PRIORITIES = frozenset({"critical", "high", "medium", "low"})


def _clean(value):
    """Return a stripped string for a value; ``None`` becomes an empty string."""
    return "" if value is None else str(value).strip()


def _status_key(value):
    """Canonicalise a status so 'In-Progress' and 'in progress' compare equal."""
    return normalise_status(_clean(value))


# ---------------------------------------------------------------------------
# Core logic: no input(), no file access, no mutation
# ---------------------------------------------------------------------------

def search_tickets(tickets, title=None, category=None, status=None, priority=None):
    """Return a NEW list of tickets matching every supplied filter.

    A filter that is ``None`` or blank means "do not filter by this field".
    The title is a case-insensitive substring match; category, status and
    priority are case-insensitive exact matches (status also accepts separator
    and case variants such as ``in_progress``).

    All supplied filters must match -- the brief requires AND, not OR. The
    returned list keeps the input order, and it holds references to the same
    ticket dictionaries, so nothing is copied and nothing is modified.
    """
    wanted_title = _clean(title).casefold()
    wanted_category = _clean(category).casefold()
    wanted_priority = _clean(priority).casefold()
    wanted_status = _status_key(status) if _clean(status) else ""

    results = []
    for ticket in tickets:
        if wanted_title and wanted_title not in _clean(ticket.get("title")).casefold():
            continue
        if wanted_category and _clean(ticket.get("category")).casefold() != wanted_category:
            continue
        if wanted_status and _status_key(ticket.get("status")) != wanted_status:
            continue
        if wanted_priority and _clean(ticket.get("priority")).casefold() != wanted_priority:
            continue
        results.append(ticket)
    return results


def sort_by_priority(tickets):
    """Return a NEW list ordered most urgent first, ties by ticket number.

    This is the ordering Requirement D asks for in the optional sorted view.
    It is deliberately separate from :func:`search_tickets` so that search has
    one job and does not silently apply an order of its own.
    """
    return sorted(
        tickets,
        key=lambda ticket: (
            PRIORITY_RANK.get(_clean(ticket.get("priority")).casefold(), len(PRIORITY_RANK)),
            ticket_number(ticket),
        ),
    )


# ---------------------------------------------------------------------------
# Menu function: called from main.py
# ---------------------------------------------------------------------------

def _ask_filter(prompt, allowed, canonicalise):
    """Ask until the answer is blank or valid. Blank means "no filter".

    The brief requires invalid filter options to be re-prompted rather than
    accepted or crashed on.
    """
    while True:
        answer = input(prompt).strip()
        if not answer:
            return ""
        value = canonicalise(answer)
        if value in allowed:
            return value
        options = ", ".join(sorted(allowed))
        print(f"  '{answer}' is not a valid option. Choose from: {options}")
        print("  Or press Enter to skip this filter.")


def _print_table(tickets):
    """Print the fields Requirement C asks the search view to display."""
    header = (f"  {'ID':<6}{'CATEGORY':<11}{'PRIORITY':<10}"
              f"{'STATUS':<12}{'ASSIGNED TO':<14}TITLE")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for ticket in tickets:
        print(f"  {_clean(ticket.get('id')):<6}"
              f"{_clean(ticket.get('category')):<11}"
              f"{_clean(ticket.get('priority')):<10}"
              f"{_clean(ticket.get('status')):<12}"
              f"{_clean(ticket.get('assigned_to')) or 'unassigned':<14}"
              f"{ticket.get('title', '')}")


def search_tickets_menu():
    """Menu option: read-only search over the stored tickets."""
    tickets = read_ticket_file()
    if not tickets:
        print("There are no tickets to search.")
        return []

    print("\nLeave a filter blank to ignore it.")
    title = input("Title contains: ")
    category = _ask_filter("Category (Network/Hardware/Software/Other): ",
                           CATEGORIES, str.casefold)
    status = _ask_filter("Status (open/in progress/resolved): ",
                         VALID_STATUSES, normalise_status)
    priority = _ask_filter("Priority (critical/high/medium/low): ",
                           PRIORITIES, str.casefold)

    matches = search_tickets(tickets, title, category, status, priority)

    if not matches:
        print("\nNo tickets match those filters.")
        return []

    if len(matches) > 1:
        answer = input("Sort results by priority instead of ticket order? (y/N): ")
        if answer.strip().casefold() == "y":
            matches = sort_by_priority(matches)

    print(f"\n{len(matches)} ticket(s) matched:")
    _print_table(matches)
    return matches
