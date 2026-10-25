"""The dry-run summary (standard view). Every value comes from the Design computed by this run;
Claude pastes it as is, so nothing has to be estimated or recalculated by hand."""
from ..config import GAP_MIN, GAP_SEARCH_MAX, LEVEL_NAMES, THIN_CRITICAL, THIN_MIN, THIN_SEARCH_MAX
from ..geometry.design import bed_share
from ..geometry.profile import bevel_height
from ..i18n import count, mm, num, pct, t, val
from ..printers import bed_label
from ..project.layout import show
from ..template.shapes import outline_counts


def md_table(title, header, rows):
    out = ["", f"### {title}", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


DECISIONS = {
    "new": "new project directory",
    "new_version": "new version: a build of this size with other settings exists and stays untouched",
    "identical": "already built with identical settings: the build will not change anything "
                 "(--overwrite rebuilds it, --new-version makes a separate copy)",
    "overwrite": "the existing build in this directory will be replaced (--overwrite)",
}


ROLES = {
    "stl": "STL model for printing",
    "preview": "preview: top view, wall cross-section, 3D model",
    "source": "template used (exact copy)",
    "imprint_source": "imprint template used (exact copy)",
    "manifest": "project manifest: parameters, results, STL check",
    "dry_run": "dry-run report with the settings to approve",
    "dry_run_preview": "2D preview from this dry run",
}


STATUSES = {
    "planned": "will be created after approval",
    "overwrite": "will be overwritten after approval (--overwrite)",
    "exists": "exists (identical build)",
    "created": "created by this dry run",
}


def summary_md(pr, command):
    """Markdown summary of one cutter for the dry run; pr.files holds the planned files."""
    item = (t("Item"), t("Value"))
    out = [t("## Project summary: {name}", name=pr.shape.name)]
    out += md_table(t("Basics"), item, _basics_rows(pr))
    out += md_table(t("Size and printing"), item, _size_rows(pr))
    out += md_table(t("Construction"), item, _construction_rows(pr))
    out += md_table(t("Geometry processing"), item, _processing_rows(pr))
    out += md_table(t("Checks"), (t("Check"), t("Result"), t("Recommended"), t("Status")), _check_rows(pr))
    out += _warnings_and_fixes(pr)
    rows = [(f"`{show(path)}`", t(ROLES[role]), t(STATUSES[status])) for path, role, status in pr.files]
    out += md_table(t("Planned files"), (t("File"), t("Contents"), t("Status")), rows)
    out += ["", f"### {t('Build command')}", "", "```bash", command, "```"]
    return "\n".join(out)


def _basics_rows(pr):
    p, k = pr.p, pr.shape
    rows = [(t("Name"), k.name)]
    if pr.total > 1:
        rows.append((t("Cutter"), t("{i} of {n}", i=pr.index, n=pr.total)))
    rows.append((t("Source"), k.source))
    rows.append((t("Printer"), bed_label(pr.bed) if pr.bed else t("not specified (bed fit not checked)")))
    rows.append((t("Orientation"), t("cookie = template (the STL model is mirrored, because the cutter is used upside down)")
                 if p.get("mirror", True) else t("model = template, not mirrored (--no-mirror): the cookie comes out mirrored")))
    rows.append((t("Stage"), t("dry run: nothing built yet")))
    rows.append((t("Project directory"), f"`{show(pr.out_dir, True)}` ({t(DECISIONS[pr.decision])})"))
    return rows


def _size_rows(pr):
    p = pr.p
    w, h = pr.cookie_dims
    fw, fh = pr.footprint_dims
    rows = [(t("Cookie size (cutting edge), W × D"), f"{num(w)} × {num(h)} mm"),
            (t("Requested size"), pr.size_note),
            (t("Overall footprint (flange and bridges), W × D"), f"{num(fw)} × {num(fh)} mm")]
    lin, area = bed_share(pr)
    if lin is not None:
        rows.append((t("Bed usage"), t("{lin} of the longer bed side, {area} of the bed area", lin=pct(lin), area=pct(area))))
    rows.append((t("Total height"), mm(p["height"])))
    rows.append((t("Print orientation"), t("flange down on the bed, cutting edge up, no supports")))
    rows.append((t("Bevel step height"), t("{v} (= layer height)", v=mm(p["step"]))))
    if pr.bed:
        rows.append((t("Bed margin"), t("{v} on each side", v=mm(p["margin"]))))
    return rows


def _construction_rows(pr):
    p = pr.p
    H, BH = p["height"], bevel_height(p)
    rows = [(t("Wall thickness"), mm(p["wall"])),
            (t("Cutting edge width"), mm(p["blade"])),
            (t("Cutting edge bevel"), t("{a}° from vertical on the outer side; inner side vertical", a=val(p["blade_angle"], 0))),
            (t("Bevel height"), t("{h} (z = {z0} to {z1} mm)", h=mm(BH, 1), z0=num(H - BH), z1=val(H))),
            (t("Flange"), t("{w} wide × {th} thick, lies on the bed", w=mm(p["flange"]), th=mm(p["flange_thickness"])))]
    rows += _imprint_rows(pr)
    rows.append((t("Holes in the template"), _holes_text(pr)))
    if pr.beams:
        rows.append((t("Bridges"), t("{bridges}, {w} wide, {th} thick (flange level)", bridges=count(len(pr.beams), "bridge"),
                                     w=mm(p["bridge_width"]), th=mm(p["flange_thickness"]))))
    else:
        rows.append((t("Bridges"), t("off (--no-bridges)") if p.get("no_bridges") else t("none needed")))
    return rows


def _imprint_rows(pr):
    p = pr.p
    if not pr.ridges:
        if p.get("imprint") == "none":
            return [(t("Imprint"), t("off (--imprint none)"))]
        return [(t("Imprint"), t("none (no inner lines in the template)"))]
    rows = [(t("Imprint"), t("{ridges}, {w0} wide at the base → {w1} at the top",
                             ridges=count(len(pr.ridges), "ridge"), w0=mm(p["imprint_width"]), w1=mm(p["imprint_tip"]))),
            (t("Imprint ridge height"), t("{z}, {d} below the cutting edge",
                                          z=mm(p["height"] - p["imprint_drop"], 1), d=mm(p["imprint_drop"])))]
    if p.get("dough"):
        rows.append((t("Imprint depth"), t("{d} in {t} dough (--dough {v})", d=mm(p["dough"] - p["imprint_drop"], 1),
                                           t=mm(p["dough"]), v=val(p["dough"], 0))))
    else:
        rows.append((t("Imprint depth"), t("dough thickness minus {d} (--dough sets it exactly)", d=mm(p["imprint_drop"]))))
    return rows


def _holes_text(pr):
    p, k = pr.p, pr.shape
    holes = []
    if k.holes_cut:
        holes.append(t("{n} cut through", n=k.holes_cut))
    if k.holes_imprint:
        holes.append(t("{n} as imprint", n=k.holes_imprint) if p.get("imprint") != "none"
                     else t("{n} left out (imprint off)", n=k.holes_imprint))
    return (", ".join(holes) if holes else t("none")) + f" (--holes {p.get('holes', 'imprint')})"


def _processing_rows(pr):
    """Smoothing and simplification at the scale of the final model."""
    p, k = pr.p, pr.shape

    def at_scale(v):
        s = t("{eff} at model scale (set: {set})", eff=mm(v * pr.rescale, 2), set=mm(v))
        if k.px_size and v > 0:
            s += t(", ≈ {px} template px", px=num(v * pr.rescale / k.px_size, 1))
        return s

    rows = [(t("Outline smoothing radius"), at_scale(p["smooth"])),
            (t("Outline simplification tolerance"), at_scale(p["simplify"]))]
    if pr.simplified:
        level, sigma, r = pr.simplified
        rows.append((t("Outline simplification level"),
                     t("{level}: wiggles averaged over {sigma}, notches and tips rounded to {r} (--simplify-level {key})",
                       level=t(LEVEL_NAMES[level]), sigma=mm(sigma * pr.rescale, 1), r=mm(r * pr.rescale, 1), key=level)))
    else:
        rows.append((t("Outline simplification level"), t("off (--simplify-level none)")))
    if pr.ridges:
        rows.append((t("Imprint simplification tolerance"), t("{v} at model scale", v=mm(p["simplify"], 2))))
    if k.px_size:
        rows.append((t("Template resolution at model scale"), t("1 px = {v}", v=mm(k.px_size, 3))))
    if pr.rescale != 1.0:
        rows.append((t("Size correction after smoothing"), f"× {num(pr.rescale, 4)}"))
    if k.threshold:
        mode, th = k.threshold
        rows.append((t("Black threshold"), t("auto (Otsu): {v}", v=val(th, 0)) if mode == "auto" else t("manual: {v}", v=val(th, 0))))
    return rows


def _check_rows(pr):
    """Measured values next to the recommended limits, with a status word."""
    p, ok = pr.p, "OK"
    thin = (t("≥ {v} (nothing thinner)", v=mm(pr.thinnest, 1)) if pr.thinnest >= THIN_SEARCH_MAX
            else f"≈ {mm(pr.thinnest, 1)}")
    gap = (t("none narrower than {v}", v=mm(GAP_SEARCH_MAX, 0)) if pr.narrowest is None
           else f"≈ {mm(pr.narrowest, 1)}")
    rows = [(t("Thinnest cookie feature"), thin, f"≥ {mm(THIN_MIN, 1)}",
             t("TOO THIN") if pr.thinnest < THIN_CRITICAL else t("DELICATE") if pr.thinnest < THIN_MIN else ok),
            (t("Narrowest notch"), gap, f"≥ {mm(GAP_MIN, 1)}",
             t("NARROW") if pr.narrowest is not None and pr.narrowest < GAP_MIN else ok)]
    if pr.bed:
        fw, fh = pr.footprint_dims
        mx, my = pr.bed[0] - 2 * p["margin"], pr.bed[1] - 2 * p["margin"]
        rows.append((t("Fits on the bed"), t("{w} × {h} mm in {bw} × {bh} mm", w=num(fw), h=num(fh), bw=val(mx, 0), bh=val(my, 0)),
                     t("{m} margin, 90° rotation allowed", m=mm(p["margin"])), ok if pr.fits else t("DOES NOT FIT")))
        if pr.bed[2]:
            rows.append((t("Height vs printer Z"), t("{h} of {z}", h=mm(p["height"]), z=mm(pr.bed[2], 0)), "—",
                         ok if pr.fits_height else t("TOO TALL")))
    n_out, n_holes = outline_counts(pr.shape.body)
    rows.append((t("Separate cutting-edge outlines"), str(n_out), "—", t("info")))
    rows.append((t("Through-holes in the cookie"), str(n_holes), "—", t("info")))
    return rows


def _warnings_and_fixes(pr):
    out = ["", f"### {t('Warnings and automatic fixes')}", "", f"**{t('Warnings')}**", ""]
    out += [f"- {o}" for o in pr.warnings] or [f"- {t('none')}"]
    out += ["", f"**{t('Automatic fixes')}**", ""]
    out += [f"- {o}" for o in pr.fixes] or [f"- {t('none')}"]
    return out


def size_note(args, target):
    if args.mode == "merge":
        if args.size not in (None, "original"):
            return t("{v}, longest side of the whole assembly", v=mm(float(args.size)))
        return t("from the placements of the parts")
    if args.size in (None, "original"):
        return t("original size from the file")
    if target is None:
        return t("{v} for the largest shape on the sheet; the others keep the sheet proportions", v=mm(float(args.size)))
    return t("{v}, longest side of the cookie", v=mm(target))
