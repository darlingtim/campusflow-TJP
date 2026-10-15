"""Report and insight generation for stored tickets.

Requirement D asks for the total ticket count, counts by status, priority
and category, an unresolved count, a resolved count and a resolution
percentage. The structured report and the printed report are both built
from the one dictionary produced by ``_build_ticket_report``: the printer
only formats, it never counts. That way the numbers a caller receives and
the numbers on screen cannot drift apart.
"""
from . import read_ticket_file as read_ticket
from .workflow import VALID_STATUSES, normalise_status

# The categories the validator accepts (see validate_ticket.py). The keys
# are lowercase because create_tickets stores the category exactly as the
# operator typed it, so "Network" and "network" must share one bucket.
CATEGORIES = ("network", "hardware", "software", "other")

PRIORITIES = ("critical", "high", "medium", "low")

# Preferred display order for statuses. Kept in step with
# workflow.VALID_STATUSES by _ordered_statuses() below, so a status added
# there can never go missing from the report.
STATUS_ORDER = ("open", "in progress", "resolved")

# Requirement D: unresolved means open plus in progress.
UNRESOLVED_STATUSES = ("open", "in progress")


def _as_text(value):
    return value if isinstance(value, str) else ""


def _status_of(ticket):
    """Return a ticket's stored status in canonical form."""
    return normalise_status(_as_text(ticket.get("status")))


def _key(value):
    """Return a lowercase grouping key, so casing never splits a bucket."""
    return _as_text(value).strip().casefold()


def _ordered_statuses():
    """Every legal status, in display order, including any newly added."""
    known = tuple(status for status in STATUS_ORDER if status in VALID_STATUSES)
    return known + tuple(sorted(VALID_STATUSES.difference(STATUS_ORDER)))


def _count(values, keys):
    """Count values into buckets seeded with keys.

    A value that is not one of the expected keys still gets its own bucket
    rather than being dropped, so the buckets always add up to the number
    of tickets counted. That is what stops the report double-counting or
    quietly losing a record.
    """
    counts = {key: 0 for key in keys}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _build_ticket_report(ticket_data):
    """Build the report dictionary. Pure: the input list is not modified."""
    by_status = _count(
        [_status_of(ticket) for ticket in ticket_data], _ordered_statuses()
    )
    by_priority = _count(
        [_key(ticket.get("priority")) for ticket in ticket_data], PRIORITIES
    )
    by_category = _count(
        [_key(ticket.get("category")) for ticket in ticket_data], CATEGORIES
    )

    total = len(ticket_data)
    resolved = by_status.get("resolved", 0)

    return {
        "total": total,
        "tickets": ticket_data,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "unresolved": sum(
            by_status.get(status, 0) for status in UNRESOLVED_STATUSES
        ),
        "resolved": resolved,
        # Requirement D: an empty dataset reports 0% rather than dividing
        # by zero.
        "resolution_percent": round(resolved / total * 100, 1) if total else 0.0,
    }


def _format_report(report):
    """Render a report dictionary as text. Formatting only, no counting."""
    lines = [
        "Ticket Report Generated.",
        "---------------------",
        f"Total tickets:  {report['total']}",
        "=======================",
        "Tickets By Status:",
        "---------------------",
    ]
    for status, count in report["by_status"].items():
        lines.append(f"{status.title()}:  {count}")

    lines.extend([
        f"Unresolved (open + in progress):  {report['unresolved']}",
        f"Resolved:  {report['resolved']}",
        f"Resolution rate:  {report['resolution_percent']}%",
        "==============================",
        "Tickets By Priority:",
        "------------------------------",
    ])
    for priority, count in report["by_priority"].items():
        lines.append(f"{priority.title()}:  {count}")

    lines.extend([
        "==============================",
        "Tickets By Category:",
        "------------------------------",
    ])
    for category, count in report["by_category"].items():
        lines.append(f"{category.title()}:  {count}")

    lines.append("==============================")
    return "\n".join(lines)


def generate_total_ticket_report(ticket_data=None):
    """Report on supplied tickets, or print the report for the stored file.

    Called with a list it returns the structured report. Called with no
    argument it reads the store and prints the same report, returning
    nothing -- the CLI path.
    """
    if ticket_data is not None:
        return _build_ticket_report(ticket_data)

    stored_tickets = read_ticket()

    if not stored_tickets:
        print("No tickets found in the report.")
        return None

    print(_format_report(_build_ticket_report(stored_tickets)))
    return None


if __name__ == "__main__":
    generate_total_ticket_report()
