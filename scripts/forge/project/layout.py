"""Output layout below ROOT (the current directory unless --output-dir):
  generated/<date>/<slug>-<size>mm[-vN].stl   every STL that passed the check, ready to print
  .work/<slug>/                               template history, reading and prepare previews
  .work/<slug>/<size>mm[-vN]/                 preview, template copy, manifest, dry-run files
The version of a size directory and of its STL is the same, so a file name points at its settings.
Paths are resolved against the current directory (the user's project), never this package's."""
import datetime
import hashlib
import json
import os
import re
import shutil
import unicodedata


GENERATED_DIR = "generated"
WORK_DIR = ".work"
REJECTED_STL_FILE = "cutter-rejected.stl"
PREVIEW_FILE = "preview.png"
MANIFEST_FILE = "project.json"
DRY_RUN_FILE = "dry-run.json"
DRY_RUN_PREVIEW_FILE = "dry-run-preview.png"
READING_FILE = "reading.png"
PREPARE_FILE = "prepare.png"
RESERVED_NAMES = {"con", "prn", "aux", "nul"} | {f"{d}{i}" for d in ("com", "lpt") for i in range(1, 10)}


def slugify(name):
    """Safe directory name: lowercase ASCII letters, digits and hyphens ('Mój renifer' -> 'moj-renifer').
    The name is not translated; names without Latin letters keep their own letters."""
    s = name.strip().lower()
    for a, b in (("ł", "l"), ("ß", "ss"), ("æ", "ae"), ("ø", "o"), ("đ", "d"), ("œ", "oe")):
        s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", s.encode("ascii", "ignore").decode()).strip("-")
    if not slug:
        slug = re.sub(r"[\W_]+", "-", unicodedata.normalize("NFC", name.strip().lower())).strip("-")
    slug = slug[:60].strip("-") or "cutter"
    return slug + "-cutter" if slug in RESERVED_NAMES else slug


def show(path, is_dir=False):
    """Path for messages: relative to the current directory when inside it."""
    a, cwd = os.path.abspath(path), os.getcwd()
    p = os.path.relpath(a, cwd) if a.startswith(cwd + os.sep) else a
    return p + "/" if is_dir else p


def portable(path):
    """Path to store in a manifest: relative to the current directory, or just the file name."""
    a, cwd = os.path.abspath(path), os.getcwd()
    return os.path.relpath(a, cwd) if a.startswith(cwd + os.sep) else os.path.basename(a)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, path)


def cutter_dir(root, slug):
    """Working directory of one cutter: ROOT/.work/<slug>/."""
    return os.path.join(root, WORK_DIR, slug)


def stl_path(root, slug, out_dir, day=None):
    """The STL of the build in out_dir: ROOT/generated/<date>/<slug>-<size>mm[-vN].stl."""
    day = day or datetime.date.today().isoformat()
    return os.path.join(root, GENERATED_DIR, day, f"{slug}-{os.path.basename(os.path.normpath(out_dir))}.stl")


def size_versions(cutter_dir, size_txt):
    """Existing version directories of one size as [(version, path)]: 100mm = 1, 100mm-v2 = 2, ..."""
    found = []
    if os.path.isdir(cutter_dir):
        for n in os.listdir(cutter_dir):
            m = re.fullmatch(rf"{re.escape(size_txt)}mm(?:-v(\d+))?", n)
            if m and os.path.isdir(os.path.join(cutter_dir, n)):
                found.append((int(m.group(1) or 1), os.path.join(cutter_dir, n)))
    return sorted(found)


def manifest_stl(d, m):
    """Path of the STL a manifest in d refers to (stored relative to d), or None."""
    rel = next((f["path"] for f in m.get("files", []) if f.get("role") == "stl"), None)
    return os.path.normpath(os.path.join(d, rel)) if rel else None


def built_manifest(d):
    """The manifest of a finished build in d whose STL still exists, or None."""
    try:
        with open(os.path.join(d, MANIFEST_FILE), encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError):
        return None
    stl = manifest_stl(d, m)
    return m if m.get("stage") == "built" and stl and os.path.exists(stl) else None


def is_free(d, stl=None):
    """A directory that holds no build (at most dry-run files) and whose STL name is not taken."""
    return not os.path.exists(os.path.join(d, MANIFEST_FILE)) and not (stl and os.path.exists(stl))


def choose_target(cutter_dir, size_txt, fingerprint, overwrite=False, new_version=False, stl_for=lambda d: None):
    """Where a build of these settings goes, and why:
    identical   - a build with the same fingerprint exists; nothing is rebuilt (unless overwrite)
    overwrite   - replace that identical build, or else the latest build of this size
    new         - first build of this size
    new_version - builds with other settings exist and stay untouched; use the next version dir"""
    versions = size_versions(cutter_dir, size_txt)
    built = [(d, m) for _, d in versions if (m := built_manifest(d))]
    same = [d for d, m in built if m.get("fingerprint") == fingerprint]
    if same and not new_version:
        return same[0], "overwrite" if overwrite else "identical"
    if overwrite and built:
        return built[-1][0], "overwrite"
    free = [d for _, d in versions if is_free(d, stl_for(d))]
    if free:
        target = free[0]
    else:
        v = versions[-1][0] + 1 if versions else 1
        while True:                             # a foreign file may hold the STL name of today
            target = os.path.join(cutter_dir, f"{size_txt}mm" if v == 1 else f"{size_txt}mm-v{v}")
            if is_free(target, stl_for(target)):
                break
            v += 1
    return target, "new_version" if built else "new"


def planned_files(pr, preview_2d):
    """Files of a dry run: the results a build would write and the dry-run files written now."""
    status = dict(new="planned", new_version="planned", identical="exists", overwrite="overwrite")[pr.decision]
    d = pr.out_dir
    files = [(pr.stl_path, "stl", status), (os.path.join(d, PREVIEW_FILE), "preview", status)]
    files += [(os.path.join(d, r["file"]), r["role"], status) for _, r in pr.sources]
    files.append((os.path.join(d, MANIFEST_FILE), "manifest", status))
    files.append((os.path.join(d, DRY_RUN_FILE), "dry_run", "created"))
    if preview_2d:
        files.append((os.path.join(d, DRY_RUN_PREVIEW_FILE), "dry_run_preview", "created"))
    return files


def template_versions(work):
    """Recorded template versions in a work dir as [(index, path)]: source-original = 0, source-vN = N."""
    found = []
    if os.path.isdir(work):
        for n in os.listdir(work):
            mt = re.fullmatch(r"source-(original|v(\d+))\.[A-Za-z0-9]+", n)
            if mt:
                found.append((0 if mt.group(1) == "original" else int(mt.group(2)), os.path.join(work, n)))
    return sorted(found)


def next_template(work, ext=".png"):
    versions = template_versions(work)
    if not versions:
        return os.path.join(work, f"source-original{ext}")
    return os.path.join(work, f"source-v{versions[-1][0] + 1}{ext}")


def record_template(work, path):
    """Keeps every distinct template a cutter was analysed with: (path of the copy, newly copied)."""
    h = sha256_file(path)
    for _, v in template_versions(work):
        if sha256_file(v) == h:
            return v, False
    os.makedirs(work, exist_ok=True)
    dest = next_template(work, os.path.splitext(path)[1].lower() or ".png")
    shutil.copyfile(path, dest)
    return dest, True
