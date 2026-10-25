"""A small calendar application using local dates and times without time zones."""

import argparse
import csv
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Event:
    id: int
    title: str
    starts_at: str


def validated_details(title: str, starts_at: str) -> tuple[str, str]:
    title = title.strip()
    if not title:
        raise ValueError("The event title cannot be empty.")
    try:
        parsed = datetime.strptime(starts_at, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ValueError("Enter a real date and time as YYYY-MM-DD HH:MM.") from exc
    if parsed.strftime("%Y-%m-%d %H:%M") != starts_at:
        raise ValueError("Use zero-padded YYYY-MM-DD HH:MM format.")
    return title, starts_at


class CalendarTracker:
    """Own event identifiers and reject invalid updates before changing state."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self._events: dict[int, Event] = {}
        self._next_id = 1
        self._storage_path = Path(storage_path) if storage_path is not None else None
        if self._storage_path is not None and self._storage_path.exists():
            self._load()

    def _load(self) -> None:
        """Reject malformed storage rather than opening an empty replacement calendar."""
        try:
            with self._storage_path.open(encoding="utf-8") as source:
                data = json.load(source)
            if not isinstance(data, dict) or data.get("schema_version") != 1:
                raise ValueError("Unsupported calendar format.")
            rows = data["events"]
            next_id = data["next_id"]
            if not isinstance(rows, list) or type(next_id) is not int or next_id < 1:
                raise ValueError("Invalid calendar data.")
            events = {}
            for row in rows:
                if not isinstance(row, dict) or set(row) != {"id", "title", "starts_at"}:
                    raise ValueError("Invalid event record.")
                event_id = row["id"]
                if type(event_id) is not int or event_id < 1 or event_id in events:
                    raise ValueError("Event identifiers must be positive and unique.")
                if not isinstance(row["title"], str) or not isinstance(row["starts_at"], str):
                    raise ValueError("Event titles and dates must be text.")
                title, starts_at = validated_details(row["title"], row["starts_at"])
                events[event_id] = Event(event_id, title, starts_at)
            if next_id <= max(events, default=0):
                raise ValueError("The next identifier would reuse an existing event ID.")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Cannot load {self._storage_path}: {exc}") from exc
        self._events, self._next_id = events, next_id

    def _commit(self, events: dict[int, Event], next_id: int) -> None:
        """Write replacement storage before making a change visible in memory."""
        if self._storage_path is not None:
            parent = self._storage_path.parent
            data = {"schema_version": 1, "next_id": next_id,
                    "events": [asdict(event) for event in events.values()]}
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=parent,
                                                 suffix=".tmp", delete=False) as destination:
                    temp_path = Path(destination.name)
                    json.dump(data, destination, indent=2, ensure_ascii=False)
                    destination.write("\n")
                    destination.flush()
                    os.fsync(destination.fileno())
                os.replace(temp_path, self._storage_path)
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
        self._events, self._next_id = events, next_id

    def add_event(self, title: str, starts_at: str) -> Event:
        title, starts_at = validated_details(title, starts_at)
        event = Event(self._next_id, title, starts_at)
        self._commit({**self._events, event.id: event}, self._next_id + 1)
        return event

    def list_events(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda event: (event.starts_at, event.id))

    def delete_event(self, event_id: int) -> Event:
        try:
            removed = self._events[event_id]
        except KeyError as exc:
            raise ValueError(f"No event has ID {event_id}.") from exc
        self._commit({key: event for key, event in self._events.items() if key != event_id}, self._next_id)
        return removed

    def edit_event(self, event_id: int, title: str, starts_at: str) -> Event:
        if event_id not in self._events:
            raise ValueError(f"No event has ID {event_id}.")
        title, starts_at = validated_details(title, starts_at)
        event = Event(event_id, title, starts_at)
        self._commit({**self._events, event_id: event}, self._next_id)
        return event

    def search_events(self, query: str) -> list[Event]:
        query = query.strip().casefold()
        if not query:
            raise ValueError("Enter at least one character to search event titles.")
        return [event for event in self.list_events() if query in event.title.casefold()]

    def export_csv(self, destination: Path) -> int:
        """Export a new file without overwriting storage or existing documents."""
        destination = Path(destination)
        if self._storage_path is not None and destination.resolve() == self._storage_path.resolve():
            raise ValueError("The export path must differ from the calendar JSON file.")
        events = self.list_events()
        # Exclusive creation also rejects a symlink to an existing file.
        output = destination.open("x", encoding="utf-8-sig", newline="")
        try:
            with output:
                writer = csv.writer(output)
                writer.writerow(["id", "title", "starts_at"])
                for event in events:
                    title = event.title
                    # Treat titles as text when opened in a spreadsheet.
                    if title.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
                        title = "'" + title
                    writer.writerow([event.id, title, event.starts_at])
        except OSError:
            destination.unlink(missing_ok=True)
            raise
        return len(events)


def show_events(events: list[Event]) -> None:
    if not events:
        print("No events found.")
    for event in events:
        print(f"{event.id}: {event.starts_at} | {event.title}")


def run_menu(tracker: CalendarTracker) -> None:
    while True:
        print("\nCalendar Tracker\n1. Add event\n2. List events\n3. Delete event"
              "\n4. Edit event\n5. Search event titles\n6. Export CSV\n0. Quit")
        try:
            choice = input("Choose an option: ").strip()
            if choice == "0":
                return
            if choice == "1":
                title = input("Title: ")
                starts_at = input("Date and time (YYYY-MM-DD HH:MM): ")
                event = tracker.add_event(title, starts_at)
                print(f"Added event {event.id}.")
            elif choice == "2":
                show_events(tracker.list_events())
            elif choice == "3":
                removed = tracker.delete_event(int(input("Event ID: ")))
                print(f"Deleted {removed.title}.")
            elif choice == "4":
                event_id = int(input("Event ID: "))
                title = input("Replacement title: ")
                starts_at = input("Replacement date and time (YYYY-MM-DD HH:MM): ")
                event = tracker.edit_event(event_id, title, starts_at)
                print(f"Updated event {event.id}.")
            elif choice == "5":
                show_events(tracker.search_events(input("Title contains: ")))
            elif choice == "6":
                destination = Path(input("New CSV file (default: events.csv): ").strip() or "events.csv")
                count = tracker.export_csv(destination)
                print(f"Exported {count} event(s) to {destination}.")
            else:
                print("Choose one of the listed options.")
        except (ValueError, OSError) as exc:
            print(f"Error: {exc}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("events.json"),
                        help="JSON calendar file (default: events.json)")
    args = parser.parse_args(argv)
    try:
        run_menu(CalendarTracker(args.data))
    except (ValueError, OSError) as exc:
        print(f"Cannot open calendar: {exc}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCalendar closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
