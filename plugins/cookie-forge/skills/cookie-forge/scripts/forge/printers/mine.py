"""The user's own printers: a markdown file outside the plugin, so updates keep it.

Default ${XDG_CONFIG_HOME:-~/.config}/cookie-forge/printers.md, or the path in $COOKIE_FORGE_PRINTERS.
Rows use the format of references/printers.md; a row naming a built-in printer may leave the
size empty."""
import os

from ..errors import fail
from .catalog import builtin_printers
from .table import Printer, exact, format_row, parse_row, resolve

ENV = "COOKIE_FORGE_PRINTERS"
HEADER = """# My printers

Printers I own, offered by the cookie-forge skill. One row per printer, in the format of the
skill's references/printers.md. The size (width × depth × height in mm) may stay empty for a
printer from that table. Notes are free text, e.g. AMS 2 Pro.

| Maker | Model | X × Y × Z | Notes |
|---|---|---|---|
"""


def user_printers_path():
    if os.environ.get(ENV):
        return os.path.abspath(os.path.expanduser(os.environ[ENV]))
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "cookie-forge", "printers.md")


def _read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def _rows(lines):
    """(line index, printer) for every printer row; a missing size comes from the built-in table."""
    builtin = builtin_printers()
    rows = []
    for i, line in enumerate(lines):
        p = parse_row(line)
        if p is None:
            continue
        if not p.sized:
            same = [b for b in resolve(builtin, p.name) if b.name.lower() == p.name.lower()]
            if same:
                p = p.with_size((same[0].x, same[0].y, same[0].z))
        rows.append((i, p))
    return rows


def load_user_printers():
    return [p for _, p in _rows(_read_lines(user_printers_path()))]


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path)


def add_user_printer(name, note=None, size=None):
    """Adds a printer, or updates the note / size of a saved one.
    Returns ('added' | 'updated' | 'unchanged', printer)."""
    path = user_printers_path()
    lines = _read_lines(path) or HEADER.rstrip("\n").split("\n")
    rows = _rows(lines)
    saved = exact([p for _, p in rows], name)
    p = saved[0] if saved else _new_printer(name, size)
    at, old = next(((i, q) for i, q in rows if q.name.lower() == p.name.lower()), (None, None))
    if old:
        new = Printer(old.maker, old.model, *(size or (old.x, old.y, old.z)),
                      note=old.note if note is None else note)
        if new == old:
            return "unchanged", old
        lines[at] = format_row(new)
        _write(path, lines)
        return "updated", new
    p = Printer(p.maker, p.model, p.x, p.y, p.z, note=note or "")
    lines.insert(rows[-1][0] + 1 if rows else _table_end(lines), format_row(p))
    _write(path, lines)
    return "added", p


def _new_printer(name, size):
    found = resolve(builtin_printers(), name)
    if len(found) == 1:
        return found[0].with_size(size) if size else found[0]
    if size:
        maker, _, model = name.strip().partition(" ")
        return Printer(maker, model or maker).with_size(size)
    if found:
        fail("ambiguous printer '%s': %s" % (name, ", ".join(p.name for p in found[:8])))
    fail(f"'{name}' is not in the printer table; give its bed with --bed WIDTHxDEPTH[xHEIGHT], e.g. --bed 350x350x340")


def _table_end(lines):
    """Index after the header separator of the table, or the end of the file (new table)."""
    for i, line in enumerate(lines):
        if line.strip().startswith("|---"):
            return i + 1
    lines += ["", "| Maker | Model | X × Y × Z | Notes |", "|---|---|---|---|"]
    return len(lines)


def remove_user_printer(name):
    path = user_printers_path()
    lines = _read_lines(path)
    rows = _rows(lines)
    found = resolve([p for _, p in rows], name)
    if not found:
        fail(f"'{name}' is not in your printers ({path})")
    if len(found) > 1:
        fail("ambiguous printer '%s': %s" % (name, ", ".join(p.name for p in found)))
    i = next(i for i, p in rows if p is found[0])
    del lines[i]
    _write(path, lines)
    return found[0]
