# Calendar Tracker AI

A small Python calendar application for a CSCI498 version control lab. Version 1
lets users add, list, and delete events through a text menu. Events stay in memory
and are cleared when the program closes.

## Run

Requires Python 3.11 or later. No third-party packages are needed.

```console
python calendar_tracker.py
```

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

The baseline and planned enhancements use AI assistance. Generated code is
reviewed and tested as each feature is added. The repository records the actual
development changes rather than separate copies of the same program.
