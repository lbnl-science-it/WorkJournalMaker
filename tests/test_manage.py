# ABOUTME: Tests for the CLI user management tool (create-admin, list-users).
# ABOUTME: Validates user creation with proper password hashing and role assignment.

import asyncio
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from web.database import DatabaseManager, UserAccount
from web.manage import create_admin, list_users


class TestCreateAdmin:
    """Tests for the create-admin CLI command."""

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_manage.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    def test_create_admin_user(self, db):
        import bcrypt
        from sqlalchemy import select

        async def _test():
            await create_admin(db, "myadmin", "securepass123")

            async with db.get_session() as session:
                stmt = select(UserAccount).where(UserAccount.username == "myadmin")
                result = await session.execute(stmt)
                user = result.scalar_one()
                assert user.role == "admin"
                assert user.is_active is True
                assert bcrypt.checkpw(b"securepass123", user.password_hash.encode())

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_create_duplicate_username_raises(self, db):
        async def _test():
            await create_admin(db, "dup", "pass1")
            with pytest.raises(ValueError):
                await create_admin(db, "dup", "pass2")

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()


class TestListUsers:
    """Tests for the list-users CLI command."""

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_manage_list.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    def test_list_empty(self, db):
        async def _test():
            users = await list_users(db)
            assert users == []

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_list_after_create(self, db):
        async def _test():
            await create_admin(db, "admin1", "pass")
            users = await list_users(db)
            assert len(users) == 1
            assert users[0]["username"] == "admin1"
            assert users[0]["role"] == "admin"
            assert "password_hash" not in users[0]

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()
