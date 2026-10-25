"""paths: where the files of a cutter go, so that nobody has to invent paths (JSON)."""
import json
import os
import re

from ..project.layout import WORK_DIR, next_template, show, slugify, template_versions


def cmd_paths(args):
    """Where the files of a cutter go, so that nobody has to invent paths (JSON)."""
    slug = slugify(args.name)
    cutter_dir = os.path.join(args.output_dir, slug)
    work = os.path.join(cutter_dir, WORK_DIR)
    print(json.dumps(dict(name=args.name, id=slug, cutter_dir=show(cutter_dir, True), work_dir=show(work, True),
                          next_template=show(next_template(work, "." + args.ext.lstrip("."))),
                          templates=[show(v) for _, v in template_versions(work)],
                          sizes=sorted(n for n in os.listdir(cutter_dir) if re.fullmatch(r"\d+mm(-v\d+)?", n))
                          if os.path.isdir(cutter_dir) else []),
                     ensure_ascii=False, indent=2))
