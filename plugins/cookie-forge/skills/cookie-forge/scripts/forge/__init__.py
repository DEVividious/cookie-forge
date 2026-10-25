"""cookie-forge: cookie cutter generator, image (PNG/JPG/PDF) -> STL.

Subdomains (dependencies only point downwards in this list):
  commands/      use cases behind the CLI: analyze, build, prepare, paths, printers
  presentation/  dry-run summary, build report, PNG previews
  project/       output layout and versions, manifest, settings from the command line
  geometry/      2D outline, blade profile, cutter design, 3D solid and STL
  template/      loading templates, contours -> shapes, preparing templates
  printers, config, i18n, errors: shared basics"""


VERSION = "1.4.0"
