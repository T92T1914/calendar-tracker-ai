"""A small calendar application using local dates and times without time zones."""

from dataclasses import dataclass
from datetime import datetime


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

    def __init__(self) -> None:
        self._events: dict[int, Event] = {}
        self._next_id = 1

    def add_event(self, title: str, starts_at: str) -> Event:
        title, starts_at = validated_details(title, starts_at)
        event = Event(self._next_id, title, starts_at)
        self._events[event.id] = event
        self._next_id += 1
        return event

    def list_events(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda event: (event.starts_at, event.id))

    def delete_event(self, event_id: int) -> Event:
        try:
            return self._events.pop(event_id)
        except KeyError as exc:
            raise ValueError(f"No event has ID {event_id}.") from exc


def show_events(events: list[Event]) -> None:
    if not events:
        print("No events found.")
    for event in events:
        print(f"{event.id}: {event.starts_at} | {event.title}")


def run_menu(tracker: CalendarTracker) -> None:
    while True:
        print("\nCalendar Tracker\n1. Add event\n2. List events\n3. Delete event\n0. Quit")
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
            else:
                print("Choose one of the listed options.")
        except (ValueError, OSError) as exc:
            print(f"Error: {exc}")


def main() -> int:
    try:
        run_menu(CalendarTracker())
    except (EOFError, KeyboardInterrupt):
        print("\nCalendar closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
