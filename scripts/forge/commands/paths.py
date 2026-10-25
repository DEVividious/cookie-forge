"""paths: actual workspace locations, including preserved preview comparisons."""
import json
import os
import re

from ..project.layout import cutter_dir, next_template, show, slugify, template_versions


def cmd_paths(args):
    slug = slugify(args.name)
    work = cutter_dir(args.output_dir, slug)
    builds = os.path.join(work, 'builds')
    previews = os.path.join(work, 'previews')
    print(json.dumps(dict(name=args.name, id=slug, layout_version=3,
                          workspace_dir=show(args.output_dir, True), cutter_dir=show(work, True),
                          exports_dir=show(os.path.join(args.output_dir, "exports"), True),
                          builds_dir=show(builds, True), previews_dir=show(previews, True),
                          next_template=show(next_template(work, '.' + args.ext.lstrip('.'))),
                          templates=[show(v) for _, v in template_versions(work)],
                          previews=[show(os.path.join(previews, n)) for n in sorted(os.listdir(previews))]
                          if os.path.isdir(previews) else [],
                          sizes=sorted(n for n in os.listdir(builds) if re.fullmatch(r'\d+mm-v\d+', n))
                          if os.path.isdir(builds) else []), ensure_ascii=False, indent=2))
