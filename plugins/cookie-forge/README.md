# Cookie Forge

Turn a drawing into a 3D-printable cookie cutter. Attach a picture and answer a few questions
about your printer, the cookie size and whether inner lines should press a pattern into the
dough. Then approve the dry-run summary and preview, and get an STL with a 0.45 mm beveled
cutting edge, a 1.2 mm wall and a 5 mm grip flange.

## Install

```bash
# Claude Code
claude plugin marketplace add DEVividious/cookie-forge
claude plugin install cookie-forge@cookie-forge

# Codex
codex plugin marketplace add DEVividious/cookie-forge
codex plugin add cookie-forge@cookie-forge
```

In a Claude Code session, `/plugin install cookie-forge --marketplace DEVividious/cookie-forge`
does both steps.

## What it runs

The skill runs one bundled Python script, `skills/cookie-forge/scripts/cookie_forge.py`, with
`uv run --locked`. On the first run, uv downloads the library versions pinned in
`cookie_forge.py.lock` from PyPI; later runs reuse its cache. The script reads the template
you point it at and writes its results to `cookie-forge-output/` in your current project. It
makes no network requests of its own, sends no data anywhere and needs no API key.

## Requirements

Python 3.10 or later and [uv](https://docs.astral.sh/uv/). Native Windows is not yet verified
end to end.

Examples, the full guide and the command-line reference:
[github.com/DEVividious/cookie-forge](https://github.com/DEVividious/cookie-forge).
