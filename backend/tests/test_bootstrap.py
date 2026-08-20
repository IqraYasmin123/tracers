"""Tests for app/auth/bootstrap.py's bootstrap_initial_admin (Module 16)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.bootstrap import bootstrap_initial_admin
from app.auth.security import verify_password
from database.models import Base, User, UserRole


def _fresh_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def test_creates_an_admin_when_no_users_exist(capsys):
    db = _fresh_session()
    assert db.query(User).count() == 0

    bootstrap_initial_admin(db)

    users = db.query(User).all()
    assert len(users) == 1
    assert users[0].role == UserRole.ADMIN


def test_prints_the_generated_password_exactly_once(capsys):
    db = _fresh_session()
    bootstrap_initial_admin(db)

    captured = capsys.readouterr()
    assert "password:" in captured.out
    assert "initial admin account was created" in captured.out


def test_the_printed_password_actually_matches_the_stored_hash(capsys):
    db = _fresh_session()
    bootstrap_initial_admin(db)

    captured = capsys.readouterr()
    password_line = next(line for line in captured.out.splitlines() if "password:" in line)
    printed_password = password_line.split("password:", 1)[1].strip()

    user = db.query(User).first()
    assert verify_password(printed_password, user.password_hash)


def test_does_nothing_if_a_user_already_exists(capsys):
    db = _fresh_session()
    existing = User(
        username="already-here",
        email="already@example.com",
        password_hash="irrelevant-for-this-test",
        role=UserRole.VIEWER,
    )
    db.add(existing)
    db.commit()

    bootstrap_initial_admin(db)

    users = db.query(User).all()
    assert len(users) == 1
    assert users[0].username == "already-here"  # untouched, not reset/overwritten

    captured = capsys.readouterr()
    assert captured.out == ""  # nothing printed — no new account was created


def test_generated_passwords_are_not_predictable(capsys):
    """Two separate bootstrap runs (against two separate empty databases) should never
    produce the same password — a fixed/predictable password would defeat the entire
    point of generating one randomly."""
    db1 = _fresh_session()
    bootstrap_initial_admin(db1)
    password1 = next(l for l in capsys.readouterr().out.splitlines() if "password:" in l)

    db2 = _fresh_session()
    bootstrap_initial_admin(db2)
    password2 = next(l for l in capsys.readouterr().out.splitlines() if "password:" in l)

    assert password1 != password2
