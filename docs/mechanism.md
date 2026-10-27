# One local event, inspectable files

This conceptual diagram follows the actual public text-menu program: validate a
title and local date/time, write schema-1 JSON, then inspect, edit, search or export
calendar order to a new CSV. It is not a screenshot or an application run.

The synthetic worked example starts with an empty calendar. `Lab review` at
`2026-11-01 09:00` receives ID 1, with `next_id` 2 and `schema_version` 1. The date
has no timezone. Read [the actual validation/storage/export code](../calendar_tracker.py)
and [temporary-file tests](../test_calendar_tracker.py) for behavior.

Persistence writes and flushes a temporary file before replacing the JSON path,
then updates memory. Corrupt input stops startup without an empty replacement.
CSV export creates a new path exclusively, writes `id,title,starts_at` in calendar
order with a UTF-8 BOM, and protects formula-leading titles in the export while
preserving stored text. This is local single-process behavior, not synchronization,
a backup service, an AI model or a browser calendar.

The static page's local Inter declarations have system fallbacks. It distributes
no font files. Its small pinned adapter records the established family source at
`7a57fe750ff50205a17e1d342106a0d3f2777159`; no theme is fetched at runtime. Obscur
is the first-visit/no-JavaScript baseline. A saved explicit Auto/Clair/Obscur choice
is optional and affects only the static explanation.

## Rebuild the graphic

The editable source is [mechanism.json](mechanism.json) and
[tools/render_mechanism.py](../tools/render_mechanism.py). Install the optional
[figure requirements](requirements-figures.txt) in an isolated authoring environment.
They are not application dependencies. Supply genuine Inter Regular 400,
SemiBold 600 and Bold 700 static TTF files from one release. No font files or
machine paths are distributed.

```console
python -m pip install -r docs/requirements-figures.txt
python tools/render_mechanism.py --font-dir /path/to/Inter/extras/ttf
python tools/render_mechanism.py --check
```

`OBSCUR_FONT_DIR` is an optional alternative to the argument. The renderer checks
actual font names, weights and Latin glyph coverage, exports opaque 1800 x 800
wide and 960-pixel-wide narrow PNG/SVG editions, and rejects labels outside the canvas.
The narrow height follows actual font bounds. The current recorded edition is 960 x 1210.
Labels use at least 30 points at 100 dpi. SVG labels are outlines from those same
files. Adjacent HTML/Markdown supplies selectable text and source links.

The generated `mechanism-rendering.json` records source/adapter hashes, font
hashes, renderer versions, layout and all four output hashes. `--check` compares
committed inputs and outputs without importing the application, downloading fonts
or silently regenerating missing files. A new presentation render is not a new
application or scientific execution. Actual receiving-page image selection,
readability and visitor font fallback remain separate checks.

