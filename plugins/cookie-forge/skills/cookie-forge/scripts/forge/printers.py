"""Printer bed sizes from references/printers.md and the --bed option."""
import os
import re

from .errors import fail
from .i18n import t, val

REFERENCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "references")


def load_printers():
    """Reads the table in references/printers.md: | Maker | Model | X×Y×Z | notes |."""
    path = os.path.join(REFERENCES, "printers.md")
    printers = []
    if not os.path.exists(path):
        return printers
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)\s*\|", line)
        if m:
            printers.append(dict(maker=m.group(1), model=m.group(2),
                                 x=int(m.group(3)), y=int(m.group(4)), z=int(m.group(5))))
    return printers


def find_printer(phrase):
    f = phrase.lower().replace("-", " ").split()
    found = []
    for d in load_printers():
        text = f"{d['maker']} {d['model']}".lower().replace("-", " ")
        if all(s in text for s in f):
            found.append(d)
    return found


def parse_bed(text):
    """'220x220' or '220x220x250' or a printer name -> (x, y, z|None, printer name|None)."""
    if not text:
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)(?:\s*[x×]\s*(\d+(?:\.\d+)?))?\s*$", text)
    if m:
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)) if m.group(3) else None, None)
    d = find_printer(text)
    if len(d) == 1:
        return (d[0]["x"], d[0]["y"], d[0]["z"], f"{d[0]['maker']} {d[0]['model']}")
    if len(d) > 1:
        fail("ambiguous printer '%s': %s" % (text, ", ".join(x["model"] for x in d[:8])))
    fail(f"unknown printer '{text}'; give the bed as WIDTHxDEPTH, e.g. --bed 220x220")


def bed_label(bed):
    x, y, z, name = bed
    size = f"{val(x, 0)} × {val(y, 0)}" + (f" × {val(z, 0)}" if z else "") + " mm"
    return f"{name} ({t('bed {size}', size=size)})" if name else t("bed {size}", size=size)
