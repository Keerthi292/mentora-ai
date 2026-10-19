"""Account commands for the terminal (run from backend/):

    uv run python -m app.manage list-users
    uv run python -m app.manage set-login --user-id 1 --email you@example.com

set-login gives an existing account (e.g. your data from before logins existed)
an email and password. The password is typed in, never passed on the command line.
"""

import argparse
import getpass
import sys

from pydantic import TypeAdapter, ValidationError

from app.database import SessionLocal
from app.models import User
from app.repositories import user_repository
from app.schemas import Email, Password
from app.security import hash_password


def list_users() -> None:
    with SessionLocal() as db:
        for user in db.query(User).order_by(User.id):
            login = "can log in" if user.password_hash else "no password yet"
            print(f"{user.id:>4}  {user.full_name:<25} {user.email:<35} {login}")


def set_login(user_id: int, email: str) -> None:
    try:
        email = TypeAdapter(Email).validate_python(email)
    except ValidationError:
        sys.exit(f"Not a valid email: {email}")
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            sys.exit(f"No user with id {user_id}. See: uv run python -m app.manage list-users")
        other = user_repository.get_user_by_email(db, email)
        if other is not None and other.id != user.id:
            sys.exit(f"{email} is already used by user {other.id}.")

        password = getpass.getpass("New password (min 8 characters): ")
        if getpass.getpass("Repeat the password: ") != password:
            sys.exit("The passwords don't match. Nothing changed.")
        try:
            TypeAdapter(Password).validate_python(password)
        except ValidationError:
            sys.exit("The password must be 8 to 128 characters. Nothing changed.")

        user_repository.update_user(db, user, {"email": email, "password_hash": hash_password(password)})
        print(f'Done: "{user.full_name}" can now log in as {email}.')


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.manage", description="Mentora AI account commands")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-users", help="Show all accounts")
    login = commands.add_parser("set-login", help="Set an account's email and password")
    login.add_argument("--user-id", type=int, required=True)
    login.add_argument("--email", required=True)
    args = parser.parse_args()

    if args.command == "list-users":
        list_users()
    else:
        set_login(args.user_id, args.email)


if __name__ == "__main__":
    main()
