"""Provision the first administrator securely from an interactive shell.

Run after applying migration 0008:
    python scripts/create_admin.py
"""
import getpass
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import crud
from app.services.admin_auth import hash_password


def main() -> None:
    email = input("Administrator email: ").strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise SystemExit("Enter a valid email address.")
    name = input("Administrator name: ").strip()
    if not name:
        raise SystemExit("Administrator name is required.")
    password = getpass.getpass("Password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if crud.get_admin_account_by_email(email):
        raise SystemExit("An administrator account already uses that email.")
    account = crud.create_admin_account(email, name, hash_password(password))
    print(f"Created administrator {account['email']} ({account['id']}).")


if __name__ == "__main__":
    main()
