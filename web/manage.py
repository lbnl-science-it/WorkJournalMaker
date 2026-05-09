# ABOUTME: CLI tool for user account management (create-admin, list-users).
# ABOUTME: Bootstraps the first admin user without requiring API authentication.

import argparse
import asyncio
import getpass
import sys
import uuid

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from web.database import DatabaseManager, UserAccount


async def create_admin(db: DatabaseManager, username: str, password: str) -> str:
    """Create an admin user account. Returns the new user's ID."""
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())

    async with db.get_session() as session:
        stmt = select(UserAccount).where(UserAccount.username == username)
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ValueError(f"Username '{username}' already exists")

        session.add(UserAccount(
            id=user_id,
            username=username,
            password_hash=pw_hash,
            role="admin",
            is_active=True,
        ))
        await session.commit()

    return user_id


async def list_users(db: DatabaseManager) -> list:
    """List all user accounts (without password hashes)."""
    async with db.get_session() as session:
        stmt = select(UserAccount).order_by(UserAccount.created_at)
        result = await session.execute(stmt)
        accounts = result.scalars().all()

    return [
        {
            "id": a.id,
            "username": a.username,
            "role": a.role,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in accounts
    ]


async def _main(args: argparse.Namespace) -> None:
    db = DatabaseManager()
    await db.initialize()

    if args.command == "create-admin":
        password = args.password or getpass.getpass("Password: ")
        user_id = await create_admin(db, args.username, password)
        print(f"Admin user '{args.username}' created (id: {user_id})")

    elif args.command == "list-users":
        users = await list_users(db)
        if not users:
            print("No users found.")
        else:
            for u in users:
                status = "active" if u["is_active"] else "disabled"
                print(f"  {u['username']}  role={u['role']}  {status}  id={u['id']}")

    if db.engine:
        await db.engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Work Journal Maker user management")
    sub = parser.add_subparsers(dest="command", required=True)

    create_parser = sub.add_parser("create-admin", help="Create an admin user")
    create_parser.add_argument("--username", required=True)
    create_parser.add_argument("--password", default=None, help="Password (prompted if omitted)")

    sub.add_parser("list-users", help="List all users")

    args = parser.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
