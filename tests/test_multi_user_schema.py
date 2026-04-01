# ABOUTME: Tests for the multi-user database schema additions.
# ABOUTME: Validates User model and user_id scoping on JournalEntryIndex.
"""Tests for multi-user database schema."""
import pytest
from datetime import datetime, date
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from web.database import Base, User, JournalEntryIndex


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


class TestUserModel:
    def test_create_user(self, session):
        """User model can be created and persisted."""
        user = User(
            id="user-123",
            email="test@lbl.gov",
            display_name="Test User",
            storage_path="/data/users/user-123/worklogs",
        )
        session.add(user)
        session.commit()

        result = session.query(User).filter_by(id="user-123").first()
        assert result is not None
        assert result.email == "test@lbl.gov"
        assert result.display_name == "Test User"

    def test_user_email_unique(self, session):
        """Email must be unique across users."""
        user1 = User(id="u1", email="same@lbl.gov", display_name="User 1")
        user2 = User(id="u2", email="same@lbl.gov", display_name="User 2")
        session.add(user1)
        session.commit()
        session.add(user2)
        with pytest.raises(Exception):
            session.commit()

    def test_local_user_default(self, session):
        """A 'local' user exists for single-user mode."""
        user = User(id="local", display_name="Local User")
        session.add(user)
        session.commit()
        result = session.query(User).filter_by(id="local").first()
        assert result is not None


class TestJournalEntryUserScope:
    def test_entry_has_user_id(self, session):
        """JournalEntryIndex has a user_id column."""
        entry = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/worklogs/worklog_2024-01-15.txt",
            user_id="local",
            has_content=True,
            week_ending_date=date(2024, 1, 19),
        )
        session.add(entry)
        session.commit()

        result = session.query(JournalEntryIndex).first()
        assert result.user_id == "local"

    def test_same_date_different_users(self, session):
        """Two users can have entries for the same date."""
        entry1 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/user1/worklog.txt",
            user_id="user-1",
            has_content=True,
            week_ending_date=date(2024, 1, 19),
        )
        entry2 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/user2/worklog.txt",
            user_id="user-2",
            has_content=True,
            week_ending_date=date(2024, 1, 19),
        )
        session.add_all([entry1, entry2])
        session.commit()

        results = session.query(JournalEntryIndex).filter_by(
            date=date(2024, 1, 15)
        ).all()
        assert len(results) == 2

    def test_same_date_same_user_rejected(self, session):
        """Same user cannot have two entries for the same date."""
        entry1 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/path1.txt",
            user_id="local",
            has_content=True,
            week_ending_date=date(2024, 1, 19),
        )
        entry2 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/path2.txt",
            user_id="local",
            has_content=True,
            week_ending_date=date(2024, 1, 19),
        )
        session.add(entry1)
        session.commit()
        session.add(entry2)
        with pytest.raises(Exception):
            session.commit()

    def test_default_user_id_is_local(self, session):
        """Entries without explicit user_id default to 'local'."""
        entry = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/worklogs/worklog.txt",
            has_content=True,
            week_ending_date=date(2024, 1, 19),
        )
        session.add(entry)
        session.commit()

        result = session.query(JournalEntryIndex).first()
        assert result.user_id == "local"
