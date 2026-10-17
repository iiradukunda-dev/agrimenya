import argparse

from app.db import crud
from app.services.whatsapp.templates import TEMPLATES


def main() -> None:
    parser = argparse.ArgumentParser(description="Register WhatsApp templates as drafts")
    parser.add_argument("--mark-approved", nargs=2, metavar=("NAME", "LANG"))
    args = parser.parse_args()
    if args.mark_approved:
        name, language = args.mark_approved
        if not crud.get_whatsapp_template(name, language):
            parser.error("Template does not exist; seed it before marking it approved")
        updated = crud.set_whatsapp_template_status(name, language, "approved")
        if not updated:
            parser.error("Template approval status was not updated")
        print(f"Marked {name} ({language}) approved; confirm Meta approval first.")
        return

    for (name, language), template in TEMPLATES.items():
        if crud.get_whatsapp_template(name, language):
            continue
        crud.upsert_whatsapp_template({
            "name": name,
            "language": language,
            **template,
            "status": "draft",
        })
        print(f"Added draft {name} ({language})")


if __name__ == "__main__":
    main()
