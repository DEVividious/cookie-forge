"""paths: where the files of a cutter go, so that nobody has to invent paths (JSON)."""
import json
import os
import re

from ..project.layout import GENERATED_DIR, cutter_dir, next_template, show, slugify, template_versions


def cmd_paths(args):
    """Where the files of a cutter go, so that nobody has to invent paths (JSON)."""
    slug = slugify(args.name)
    work = cutter_dir(args.output_dir, slug)
    print(json.dumps(dict(name=args.name, id=slug, cutter_dir=show(work, True),
                          generated_dir=show(os.path.join(args.output_dir, GENERATED_DIR), True),
                          next_template=show(next_template(work, "." + args.ext.lstrip("."))),
                          templates=[show(v) for _, v in template_versions(work)],
                          sizes=sorted(n for n in os.listdir(work) if re.fullmatch(r"\d+mm(-v\d+)?", n))
                          if os.path.isdir(work) else []),
                     ensure_ascii=False, indent=2))
