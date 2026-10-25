"""The short report after a build, and the machine-readable result (--json)."""
from ..i18n import num, t
from ..printers import bed_label
from ..project.layout import show


def build_report(pr, chk, ok, matches_dry_run):
    """Short report after a build (or after a build that was not needed), with real paths."""
    out = []
    if pr.decision == "identical":
        out += [t("## Cutter {name}: already built", name=pr.shape.name), "",
                t("Nothing was rebuilt: this directory already holds a build with identical settings. "
                  "Use --overwrite to rebuild it in place or --new-version for a separate copy.")]
    else:
        out.append(t("## Cutter {name}: ready", name=pr.shape.name) if ok else t("## Cutter {name}: PROBLEM", name=pr.shape.name))
    out.append("")
    w, h = pr.cookie_dims
    out.append(f"- {t('Cookie size')}: {num(w)} × {num(h)} mm")
    out.append(f"- {t('Printer')}: {bed_label(pr.bed) if pr.bed else t('not specified (bed fit not checked)')}")
    if chk:
        out.append("- " + t("STL check: {status} ({tight}, {bodies} solid(s), {tri} triangles, {vol} cm³ ≈ {mass} g PLA)",
                            status="OK" if ok else t("PROBLEM"),
                            tight=t("watertight") if chk["watertight"] else t("NOT WATERTIGHT"),
                            bodies=chk["bodies"], tri=chk["triangles"], vol=num(chk["volume_cm3"]),
                            mass=num(chk["pla_mass_g"], 0)))
    for wmsg in pr.warnings:
        out.append(f"- {t('Warning')}: {wmsg}")
    if matches_dry_run is False:
        out.append(f"- {t('Note')}: {t('these settings were not shown in a dry run before the build')}")
    if pr.decision == "new_version":
        out.append(f"- {t('Note')}: {t('a build of this size with other settings exists and was left untouched; this is a new version')}")
    out += ["", f"{t('Files')}:", ""]
    # the template copy and project.json stay in the build directory; --json lists every file
    out += [f"- `{show(path)}`: {t(REPORT_ROLES[role])}" for path, role, _ in pr.files if role in REPORT_ROLES]
    return "\n".join(out)


REPORT_ROLES = {
    "stl": "3D print model",
    "preview": "cutter preview",
}


def cutter_result(pr):
    """Machine-readable result of one cutter (--json)."""
    return dict(name=pr.shape.name, id=pr.slug, dir=show(pr.out_dir, True), decision=pr.decision,
                files=[dict(path=show(path), role=role, status=status) for path, role, status in pr.files],
                warnings=[str(m) for m in pr.warnings], fixes=[str(m) for m in pr.fixes])
