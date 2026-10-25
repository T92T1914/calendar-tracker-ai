"""Behavior checks for the calendar application. No real calendar data is used."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from calendar_tracker import CalendarTracker, run_menu


class CalendarTests(unittest.TestCase):
    def test_add_and_list_in_date_order(self):
        tracker = CalendarTracker()
        later = tracker.add_event("  Study session  ", "2026-11-02 18:30")
        earlier = tracker.add_event("Assignment due", "2026-11-01 23:59")
        self.assertEqual(tracker.list_events(), [earlier, later])
        self.assertEqual(later.title, "Study session")

    def test_delete_does_not_reuse_identifiers(self):
        tracker = CalendarTracker()
        first = tracker.add_event("First", "2026-11-01 09:00")
        self.assertEqual(tracker.delete_event(first.id), first)
        self.assertEqual(tracker.list_events(), [])
        self.assertEqual(tracker.add_event("Second", "2026-11-01 10:00").id, 2)
        with self.assertRaises(ValueError):
            tracker.delete_event(first.id)

    def test_invalid_inputs_leave_state_unchanged(self):
        tracker = CalendarTracker()
        for title, date in [(" ", "2026-11-01 09:00"), ("Bad", "2026-02-30 09:00"),
                            ("Bad", "2026-1-1 9:00"), ("Bad", "2026-11-01 25:00")]:
            with self.subTest(title=title, date=date), self.assertRaises(ValueError):
                tracker.add_event(title, date)
        self.assertEqual(tracker.list_events(), [])
        self.assertEqual(tracker.add_event("Valid", "2026-11-01 09:00").id, 1)

    def test_menu_add_list_delete_and_quit(self):
        tracker = CalendarTracker()
        answers = ["1", "Demo event", "2026-11-01 09:00", "2", "3", "1", "0"]
        output = io.StringIO()
        with patch("builtins.input", side_effect=answers), redirect_stdout(output):
            run_menu(tracker)
        self.assertIn("Added event 1.", output.getvalue())
        self.assertIn("2026-11-01 09:00 | Demo event", output.getvalue())
        self.assertIn("Deleted Demo event.", output.getvalue())
        self.assertEqual(tracker.list_events(), [])

    def test_menu_recovers_from_invalid_input(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["9", "3", "invalid", "0"]), redirect_stdout(output):
            run_menu(CalendarTracker())
        self.assertIn("Choose one of the listed options.", output.getvalue())
        self.assertIn("Error:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
