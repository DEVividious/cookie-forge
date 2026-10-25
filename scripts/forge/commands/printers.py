"""printers: look up a printer and its bed size."""
from ..i18n import t
from ..printers import find_printer, load_printers


def cmd_printers(args):
    d = find_printer(" ".join(args.phrase)) if args.phrase else load_printers()
    if not d:
        print("Unknown printer. Ask the user for the bed size (width × depth in mm).")
        return
    print("| " + " | ".join([t("Maker"), t("Model"), t("Bed X × Y × Z (mm)")]) + " |")
    print("|---|---|---|")
    for x in d:
        print(f"| {x['maker']} | {x['model']} | {x['x']} × {x['y']} × {x['z']} |")
