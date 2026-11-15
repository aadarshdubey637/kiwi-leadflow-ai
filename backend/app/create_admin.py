"""CLI: python -m app.create_admin <username> <email>   (password is prompted, never passed on the command line)"""
import getpass
import sys

from app.database.connection import SessionLocal, init_db
from app.services.auth_service import create_admin


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python -m app.create_admin <username> <email>")
    password = getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8:
        sys.exit("Password too short")
    init_db()
    with SessionLocal() as db:
        admin = create_admin(db, sys.argv[1], sys.argv[2], password)
    print(f"Created admin '{admin.username}'")


if __name__ == "__main__":
    main()
