"""Printer rows in markdown tables: | Maker | Model | X × Y × Z | Notes |."""
import re
from dataclasses import dataclass, replace

SIZE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)(?:\s*[x×]\s*(\d+(?:\.\d+)?))?\s*$")


@dataclass(frozen=True)
class Printer:
    maker: str
    model: str
    x: float = None       # bed size in mm; None until known
    y: float = None
    z: float = None       # height, may be unknown
    note: str = ""

    @property
    def name(self):
        return f"{self.maker} {self.model}".strip()

    @property
    def sized(self):
        return self.x is not None

    def with_size(self, size):
        return replace(self, x=size[0], y=size[1], z=size[2])


def number(s):
    """'220' -> 220, '220.5' -> 220.5 (whole numbers stay int, as in the build fingerprint)."""
    return int(s) if s.isdigit() else float(s)


def parse_size(text):
    """'220x220' or '220 × 220 × 250' -> (x, y, z|None); anything else -> None."""
    m = SIZE.match(text or "")
    if not m:
        return None
    return number(m.group(1)), number(m.group(2)), number(m.group(3)) if m.group(3) else None


def format_size(p, sep=" × "):
    if not p.sized:
        return ""
    return sep.join(f"{v:g}" for v in (p.x, p.y, p.z) if v is not None)


def parse_row(line):
    """A table row -> Printer, or None for other lines (text, header, separator).
    The size cell may be empty: the size is then looked up in the built-in table."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells = [c.strip() for c in s.strip("|").split("|")]
    if len(cells) < 3 or not cells[0] or not cells[1] or cells[0].startswith("-"):
        return None
    size = parse_size(cells[2])
    if cells[2] and not size:
        return None    # the header row
    p = Printer(cells[0], cells[1], note=cells[3] if len(cells) > 3 else "")
    return p.with_size(size) if size else p


def format_row(p):
    return f"| {p.maker} | {p.model} | {format_size(p)} | {p.note} |".replace("|  |", "| |")


def _norm(text):
    return " ".join(text.lower().replace("-", " ").split())


def search(printers, phrase):
    """Every printer whose maker and model contain all words of the phrase."""
    words = _norm(phrase).split()
    return [p for p in printers if all(w in _norm(p.name) for w in words)]


def exact(printers, phrase):
    """Printers whose model or maker + model is the phrase."""
    return [p for p in printers if _norm(phrase) in (_norm(p.model), _norm(p.name))]


def resolve(printers, phrase):
    """Printers the phrase names: an exact match wins over partial ones, so 'K1' is the
    Creality K1 and not also the K1C."""
    return exact(printers, phrase) or search(printers, phrase)
