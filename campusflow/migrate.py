"""One-time migration of the ticket store to the current on-disk format.

Decision D2 in ``docs/design-decisions.md`` requires the stored data to be
migrated once and the validator and loader to stay strict afterwards:

* ``affected_users`` becomes an integer instead of the numeric string the
  original file shipped (``"12"`` -> ``12``).
* every record gains a ``notes`` list.

The migration is deliberately separate from normal application startup. Run it
by hand, once, against a store written by an older version:

    python -m campusflow.migrate            # migrates ./tickets.json
    python -m campusflow.migrate path.json  # migrates another store

The original file is copied to ``<path>.bak`` before anything is rewritten, as
D2 requires source data to be backed up first. Records whose ``affected_users``
is not a whole number are left untouched so the strict loader rejects them
rather than silently repairing them.
"""

import json
import shutil
import sys
from pathlib import Path

DEFAULT_TICKET_FILE = "tickets.json"


def migrate_ticket(record):
    """Return ``record`` in the current format.

    Converts a numeric-string ``affected_users`` to an integer and adds an
    empty ``notes`` list when the key is missing.
    """
    migrated = dict(record)

    affected_users = migrated.get("affected_users")
    if isinstance(affected_users, str):
        text = affected_users.strip()
        if text.lstrip("-").isdigit():
            migrated["affected_users"] = int(text)

    migrated.setdefault("notes", [])
    return migrated


def migrate_tickets_file(path=DEFAULT_TICKET_FILE, backup=True):
    """Migrate the ticket store at ``path`` in place.

    Returns the number of records written. Raises ``json.JSONDecodeError`` when
    the file is not valid JSON, leaving it untouched.
    """
    ticket_file = Path(path)
    records = json.loads(ticket_file.read_text(encoding="utf-8"))

    if not isinstance(records, list):
        raise TypeError(f"{path} does not contain a list of tickets.")

    if backup:
        shutil.copyfile(ticket_file, ticket_file.with_name(ticket_file.name + ".bak"))

    migrated = [migrate_ticket(record) for record in records]
    ticket_file.write_text(
        json.dumps(migrated, indent=4) + "\n",
        encoding="utf-8",
    )
    return len(migrated)


def main(argv=None):
    """Run the migration from the command line."""
    arguments = sys.argv[1:] if argv is None else argv
    path = arguments[0] if arguments else DEFAULT_TICKET_FILE

    count = migrate_tickets_file(path)
    print(f"Migrated {count} ticket(s) in {path}. Backup written to {path}.bak.")
    return count


if __name__ == "__main__":
    main()
