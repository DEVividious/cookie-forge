"""Printers and bed sizes: the built-in table (references/printers.md), the user's own printers
file and the --bed option."""
from ..errors import fail
from ..i18n import t, val
from .catalog import builtin_printers
from .mine import add_user_printer, load_user_printers, remove_user_printer, user_printers_path
from .table import format_size, parse_size, resolve, search

__all__ = ["add_user_printer", "bed_label", "builtin_printers", "find_printers", "format_size",
           "load_user_printers", "parse_bed", "parse_size", "remove_user_printer", "user_printers_path"]


def find_printers(phrase):
    """Search for `printers phrase`: the user's printers first, then the built-in table."""
    mine = search(load_user_printers(), phrase)
    names = {p.name.lower() for p in mine}
    return mine + [p for p in search(builtin_printers(), phrase) if p.name.lower() not in names]


def parse_bed(text):
    """'220x220' or '220x220x250' or a printer name -> (x, y, z|None, printer name|None).
    A name is looked up in the user's printers first, then in the built-in table."""
    if not text:
        return None
    size = parse_size(text)
    if size:
        return (float(size[0]), float(size[1]), float(size[2]) if size[2] is not None else None, None)
    found = resolve(load_user_printers(), text) or resolve(builtin_printers(), text)
    if len(found) == 1:
        p = found[0]
        if not p.sized:
            fail(f"{p.name} in {user_printers_path()} has no bed size; add it as WIDTH × DEPTH × HEIGHT in mm")
        return (p.x, p.y, p.z, p.name)
    if len(found) > 1:
        fail("ambiguous printer '%s': %s" % (text, ", ".join(p.name for p in found[:8])))
    fail(f"unknown printer '{text}'; give the bed as WIDTHxDEPTH, e.g. --bed 220x220")


def bed_label(bed):
    x, y, z, name = bed
    size = f"{val(x, 0)} × {val(y, 0)}" + (f" × {val(z, 0)}" if z else "") + " mm"
    return f"{name} ({t('bed {size}', size=size)})" if name else t("bed {size}", size=size)
