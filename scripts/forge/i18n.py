"""Output language (--lang): messages are written in English, locale_pl holds the Polish versions."""
import os
from contextlib import contextmanager

from .locale_pl import PL


LANG = "en"


def set_language(lang):
    global LANG
    LANG = lang


def t(text, /, **kw):
    if LANG == "pl":
        tr = PL.get(text)
        if tr is None and os.environ.get("COOKIE_FORGE_STRICT"):
            raise KeyError(f"missing Polish translation: {text!r}")
        text = tr or text
    return text.format(**kw) if kw else text


def num(x, d=1):
    """Number with d decimals and the decimal separator of the output language."""
    s = f"{x:.{d}f}"
    return s.replace(".", ",") if LANG == "pl" else s


def val(x, min_d=1, max_d=3):
    """Parameter value as given (no rounding beyond max_d), e.g. 0.45, 18.0, 0.08."""
    s = f"{x:.{max_d}f}"
    whole, frac = s.split(".") if "." in s else (s, "")
    frac = frac.rstrip("0").ljust(min_d, "0")
    s = whole + ("." + frac if frac else "")
    return s.replace(".", ",") if LANG == "pl" else s


def pct(x):
    return f"{x:.0f} %" if LANG == "pl" else f"{x:.0f}%"


def mm(x, d=None):
    """Length in mm: parameters as given (d=None), measurements with d decimals."""
    return f"{val(x) if d is None else num(x, d)} mm"


class Msg:
    """A warning or note rendered when printed: in the output language for the summary, in English
    for the manifest. Callable arguments are formatted at render time (numbers, plurals)."""

    def __init__(self, text, **kw):
        self.text, self.kw = text, kw

    def __str__(self):
        return t(self.text, **{k: v() if callable(v) else v for k, v in self.kw.items()})


@contextmanager
def english():
    global LANG
    old, LANG = LANG, "en"
    try:
        yield
    finally:
        LANG = old


def unique_msgs(msgs):
    return list({str(m): m for m in msgs}.values())


NOUNS = {
    "bridge": (("bridge", "bridges"), ("mostek", "mostki", "mostków")),
    "ridge": (("ridge", "ridges"), ("grzbiet", "grzbiety", "grzbietów")),
    "speck": (("small speck", "small specks"), ("drobną plamkę", "drobne plamki", "drobnych plamek")),
    "separate shape": (("separate shape", "separate shapes"), ("osobny kształt", "osobne kształty", "osobnych kształtów")),
}


def count(n, noun):
    en, pl = NOUNS[noun]
    if LANG == "pl":
        if n == 1:
            form = pl[0]
        elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            form = pl[1]
        else:
            form = pl[2]
    else:
        form = en[0] if n == 1 else en[1]
    return f"{n} {form}"
