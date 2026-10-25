# Calendar Tracker AI

A small Python calendar application for a CSCI498 version control lab. Use a text
menu to add, list, delete, edit, and search events. Changes are saved to JSON, and
events can be exported to CSV for inspection in a spreadsheet.

## Run

Requires Python 3.11 or later. No third-party packages are needed.

```console
python calendar_tracker.py
```

The app saves changes to `events.json` in the current directory. Use
`python calendar_tracker.py --data my_calendar.json` to choose another file.
Corrupt input stops startup without overwriting the original. Writes replace the
file only after the new data has been written successfully. This is a local,
single-process calendar. Do not open the same data file in multiple instances.

Menu option 6 exports `id`, `title`, and `starts_at` columns in calendar order.
Choose a new destination filename. Existing files are never overwritten. CSV
uses UTF-8 with a byte order mark for spreadsheet compatibility. Titles beginning
with a spreadsheet formula character receive a leading apostrophe in the export,
while the saved calendar keeps the original title.

Enter dates and local times in `YYYY-MM-DD HH:MM` format, such as
`2026-11-01 09:00`. Event identifiers remain stable during a session. The app does
not connect to an online calendar or handle time zones.

## Check behavior

```console
python -m unittest -v
```

Tests use temporary files and synthetic events. They cover input validation,
ordering, deletion, persistence failures, editing, title search, CSV quoting,
and the menu. GitHub Actions runs the suite for changes to main and pull requests.

## Version history

| Version | Change |
| --- | --- |
| v1 | Add, list, and delete events in memory |
| v2 | Save and load events in JSON |
| v3 | Edit an existing event by its stable identifier |
| v4 | Search event titles without case sensitivity |
| v5 | Export events to a new CSV file |

Each version has an annotated tag. Versions 2 through 5 were developed on separate
feature branches and merged through pull requests. Inspect [v1 versus v3](https://github.com/T92T1914/calendar-tracker-ai/compare/v1...v3)
or [v1 versus v5](https://github.com/T92T1914/calendar-tracker-ai/compare/v1...v5) for cumulative changes. Tags identify the
completed versions even after the main branch advances.

The baseline and planned enhancements use AI assistance. Generated code is
reviewed and tested as each feature is added. The repository records the actual
development changes rather than separate copies of the same program.
