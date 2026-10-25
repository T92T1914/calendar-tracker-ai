# Calendar Tracker AI

A small Python calendar application for a CSCI498 version control lab. Version 1
lets users add, list, and delete events through a text menu. Version 2 adds JSON
storage so events remain available when the program restarts. Version 3 adds
editing of an existing event's title and date without changing its identifier.

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

Enter dates and local times in `YYYY-MM-DD HH:MM` format, such as
`2026-11-01 09:00`. Event identifiers remain stable during a session. The app does
not connect to an online calendar or handle time zones.

## Check behavior

```console
python -m unittest -v
```

Tests use synthetic events and check validation, ordering, deletion, and the menu.

## Version history

| Version | Change |
| --- | --- |
| v1 | Add, list, and delete events in memory |
| v2 | Save and load events in JSON |
| v3 | Edit an existing event by its stable identifier |

The baseline and planned enhancements use AI assistance. Generated code is
reviewed and tested as each feature is added. The repository records the actual
development changes rather than separate copies of the same program.
