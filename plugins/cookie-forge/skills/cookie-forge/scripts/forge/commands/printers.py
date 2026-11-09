"""printers: look up a printer and its bed size; list, add and remove the user's own printers."""
from ..errors import fail
from ..i18n import t
from ..printers import (add_user_printer, find_printers, format_size, load_user_printers, parse_size,
                        remove_user_printer, user_printers_path)

ADDED = {
    "added": "Added {printer} to your printers ({path}).",
    "updated": "Updated {printer} in your printers ({path}).",
    "unchanged": "{printer} is already in your printers ({path}).",
}


def cmd_printers(args):
    if args.add:
        size = None
        if args.bed:
            size = parse_size(args.bed) or fail("--bed is WIDTHxDEPTH[xHEIGHT] in mm, e.g. 350x350x340")
        status, p = add_user_printer(args.add, note=args.note, size=size)
        print(t(ADDED[status], printer=p.name, path=user_printers_path()))
    elif args.remove:
        p = remove_user_printer(args.remove)
        print(t("Removed {printer} from your printers ({path}).", printer=p.name, path=user_printers_path()))
    elif args.mine:
        print_mine()
    else:
        print_search(" ".join(args.phrase))


def print_mine():
    path = user_printers_path()
    mine = load_user_printers()
    if not mine:
        print(t("No saved printers yet ({path}).", path=path))
        return
    print(t("Your printers ({path}):", path=path) + "\n")
    print("| " + " | ".join([t("Maker"), t("Model"), t("Bed X × Y × Z (mm)"), t("Notes")]) + " |")
    print("|---|---|---|---|")
    for p in mine:
        print(f"| {p.maker} | {p.model} | {format_size(p) or '?'} | {p.note} |".replace("|  |", "| |"))
    for p in mine:
        if not p.sized:
            print("\n" + t("Bed size unknown for {printer}: add it to the file as width × depth × height in mm.",
                           printer=p.name))


def print_search(phrase):
    found = find_printers(phrase)
    if not found:
        print("Unknown printer. Ask the user for the bed size (width × depth in mm).")
        return
    print("| " + " | ".join([t("Maker"), t("Model"), t("Bed X × Y × Z (mm)")]) + " |")
    print("|---|---|---|")
    for p in found:
        print(f"| {p.maker} | {p.model} | {format_size(p) or '?'} |")
