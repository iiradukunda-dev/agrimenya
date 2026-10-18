"""Emergency admin password recovery from a trusted backend shell.

Use only when the configured recovery email is unavailable:
    python scripts/reset_admin_password.py admin@example.org
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import crud
from app.services.admin_auth import hash_password


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/reset_admin_password.py ADMIN_EMAIL")
    email = sys.argv[1].strip().lower()
    account = crud.get_admin_account_by_email(email)
    if not account:
        raise SystemExit("Administrator account not found.")
    password = getpass.getpass("New password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    crud.update_admin_password(str(account["id"]), hash_password(password))
    crud.invalidate_admin_password_reset_tokens(str(account["id"]))
    print(f"Password reset for {email}; all existing sessions were revoked.")


if __name__ == "__main__":
    main()
