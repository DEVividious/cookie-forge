"""The built-in bed table in references/printers.md."""
import os

from .table import parse_row

REFERENCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "references")


def builtin_printers():
    path = os.path.join(REFERENCES, "printers.md")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [p for p in map(parse_row, f) if p and p.sized]
