"""Behavior checks for the calendar application. No real calendar data is used."""

import io
import csv
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from calendar_tracker import CalendarTracker, run_menu


class CalendarTests(unittest.TestCase):
    def test_csv_export_quotes_text_and_keeps_date_order(self):
        tracker = CalendarTracker()
        tracker.add_event('Résumé, "review"', "2026-11-02 10:00")
        tracker.add_event("Earlier", "2026-11-01 09:00")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            self.assertEqual(tracker.export_csv(path), 2)
            with path.open(encoding="utf-8-sig", newline="") as source:
                rows = list(csv.reader(source))
            self.assertEqual(rows, [["id", "title", "starts_at"],
                                    ["2", "Earlier", "2026-11-01 09:00"],
                                    ["1", 'Résumé, "review"', "2026-11-02 10:00"]])

    def test_csv_export_protects_spreadsheet_formula_titles(self):
        tracker = CalendarTracker()
        for title in ["=SUM(1,2)", "+123", "-123", "@SUM(A1:A2)"]:
            tracker.add_event(title, "2026-11-01 09:00")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "safe.csv"
            tracker.export_csv(path)
            with path.open(encoding="utf-8-sig", newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertTrue(all(row["title"].startswith("'") for row in rows))
            self.assertEqual(tracker.list_events()[0].title, "=SUM(1,2)")

    def test_csv_export_refuses_to_overwrite_calendar_or_other_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            tracker = CalendarTracker(path)
            tracker.add_event("Keep", "2026-11-01 09:00")
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                tracker.export_csv(path)
            self.assertEqual(path.read_bytes(), original)
            existing = Path(directory) / "existing.csv"
            existing.write_text("Keep this")
            with self.assertRaises(FileExistsError):
                tracker.export_csv(existing)
            self.assertEqual(existing.read_text(), "Keep this")

    def test_csv_export_cannot_take_unused_calendar_storage_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new_calendar.json"
            tracker = CalendarTracker(path)
            with self.assertRaises(ValueError):
                tracker.export_csv(path.parent / "." / path.name)
            self.assertFalse(path.exists())
            self.assertEqual(CalendarTracker(path).list_events(), [])

    def test_empty_calendar_exports_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.csv"
            self.assertEqual(CalendarTracker().export_csv(path), 0)
            self.assertEqual(path.read_text(encoding="utf-8-sig"), "id,title,starts_at\n")

    def test_csv_export_menu_creates_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu.csv"
            output = io.StringIO()
            with patch("builtins.input", side_effect=["6", str(path), "0"]), redirect_stdout(output):
                run_menu(CalendarTracker())
            self.assertTrue(path.is_file())
            self.assertIn("Exported 0 event(s)", output.getvalue())

    def test_search_is_case_insensitive_and_ordered(self):
        tracker = CalendarTracker()
        later = tracker.add_event("Study CSCI498", "2026-11-03 18:00")
        earlier = tracker.add_event("CSCI498 lab", "2026-11-01 18:00")
        tracker.add_event("Other class", "2026-11-02 18:00")
        self.assertEqual(tracker.search_events(" csci498 "), [earlier, later])

    def test_search_handles_unicode_and_no_match(self):
        tracker = CalendarTracker()
        event = tracker.add_event("Résumé review", "2026-11-01 09:00")
        self.assertEqual(tracker.search_events("RÉSUMÉ"), [event])
        self.assertEqual(tracker.search_events("Missing"), [])

    def test_empty_search_is_rejected(self):
        with self.assertRaises(ValueError):
            CalendarTracker().search_events("  ")

    def test_search_menu_displays_only_matches(self):
        tracker = CalendarTracker()
        tracker.add_event("Match me", "2026-11-01 09:00")
        tracker.add_event("Unrelated", "2026-11-02 09:00")
        output = io.StringIO()
        with patch("builtins.input", side_effect=["5", "MATCH", "0"]), redirect_stdout(output):
            run_menu(tracker)
        self.assertIn("Match me", output.getvalue())
        self.assertNotIn("Unrelated", output.getvalue())

    def test_edit_keeps_identifier_and_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            tracker = CalendarTracker(path)
            first = tracker.add_event("Before", "2026-11-01 09:00")
            updated = tracker.edit_event(first.id, " After ", "2026-11-03 14:00")
            self.assertEqual((updated.id, updated.title, updated.starts_at), (1, "After", "2026-11-03 14:00"))
            self.assertEqual(CalendarTracker(path).list_events(), [updated])
            self.assertEqual(tracker.add_event("Next", "2026-11-04 09:00").id, 2)

    def test_invalid_edit_keeps_original_event(self):
        tracker = CalendarTracker()
        event = tracker.add_event("Keep", "2026-11-01 09:00")
        with self.assertRaises(ValueError):
            tracker.edit_event(event.id, "", "2026-11-03 09:00")
        with self.assertRaises(ValueError):
            tracker.edit_event(99, "Missing", "2026-11-03 09:00")
        self.assertEqual(tracker.list_events(), [event])

    def test_edit_menu_changes_event(self):
        tracker = CalendarTracker()
        tracker.add_event("Before", "2026-11-01 09:00")
        answers = ["4", "1", "After", "2026-11-02 10:00", "0"]
        with patch("builtins.input", side_effect=answers), redirect_stdout(io.StringIO()):
            run_menu(tracker)
        self.assertEqual(tracker.list_events()[0].title, "After")

    def test_storage_survives_restart_and_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            tracker = CalendarTracker(path)
            first = tracker.add_event("Résumé review", "2026-11-01 09:00")
            restored = CalendarTracker(path)
            self.assertEqual(restored.list_events(), [first])
            restored.delete_event(first.id)
            again = CalendarTracker(path)
            self.assertEqual(again.list_events(), [])
            self.assertEqual(again.add_event("Next", "2026-11-02 09:00").id, 2)

    def test_corrupt_storage_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                CalendarTracker(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_invalid_storage_identifiers_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            event = {"id": 1, "title": "Demo", "starts_at": "2026-11-01 09:00"}
            for rows, next_id in [([event, event], 2), ([event], 1), ([], True)]:
                path.write_text(json.dumps({"schema_version": 1, "next_id": next_id, "events": rows}))
                with self.subTest(rows=rows, next_id=next_id), self.assertRaises(ValueError):
                    CalendarTracker(path)

    def test_failed_save_keeps_memory_and_original_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            tracker = CalendarTracker(path)
            first = tracker.add_event("Keep", "2026-11-01 09:00")
            original = path.read_bytes()
            with patch("calendar_tracker.os.replace", side_effect=OSError("Write failed")):
                with self.assertRaises(OSError):
                    tracker.add_event("Rejected", "2026-11-02 09:00")
            self.assertEqual(tracker.list_events(), [first])
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

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
