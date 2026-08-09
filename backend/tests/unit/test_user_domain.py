from datetime import datetime, timezone

import pytest

from app.modules.users.domain.errors import InactiveUserCannotBePromoted
from app.modules.users.domain.events import (
    UserDisabled,
    UserPromotedToAdmin,
    UserRegistered,
)
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    Authority,
    Email,
    HashedPassword,
    Nickname,
    RawPassword,
)
from app.shared.ids import new_uuid


def test_email_normalises_and_validates():
    e = Email("  Alice@Example.COM  ")
    assert e.value == "alice@example.com"


def test_email_rejects_garbage():
    with pytest.raises(ValueError):
        Email("not-an-email")


def test_nickname_rejects_special_chars():
    with pytest.raises(ValueError):
        Nickname("alice!!")


def test_raw_password_requires_letter_and_digit():
    with pytest.raises(ValueError):
        RawPassword("alphabetonly")
    with pytest.raises(ValueError):
        RawPassword("12345678")
    RawPassword("hunter22!")  # passes


def test_user_promote_to_admin_flips_flags():
    user_id = new_uuid()
    registered_at = datetime.now(timezone.utc)
    promoted_at = datetime.now(timezone.utc)
    user = User.register(
        user_id=user_id,
        email=Email("a@b.com"),
        nickname=Nickname("alice"),
        password_hash=HashedPassword("hash"),
        occurred_at=registered_at,
    )
    user.pull_events()

    assert user.authority is Authority.USER and not user.is_admin
    user.promote_to_admin(occurred_at=promoted_at)

    assert user.authority is Authority.ADMIN and user.is_admin
    assert user.pull_events() == [
        UserPromotedToAdmin(user_id=user_id, occurred_at=promoted_at)
    ]


def test_user_promote_to_admin_is_idempotent():
    now = datetime.now(timezone.utc)
    user_id = new_uuid()
    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
                nickname="alice",
                password_hash="hash",
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=now,
            ),
            UserPromotedToAdmin(user_id=user_id, occurred_at=now),
        ]
    )

    user.promote_to_admin(occurred_at=now)

    assert user.pull_events() == []


def test_user_promote_to_admin_rejects_inactive_user():
    now = datetime.now(timezone.utc)
    user_id = new_uuid()
    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
                nickname="alice",
                password_hash="hash",
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=now,
            ),
            UserDisabled(user_id=user_id, occurred_at=now),
        ]
    )

    with pytest.raises(InactiveUserCannotBePromoted):
        user.promote_to_admin(occurred_at=now)


def test_user_disable_records_user_disabled_event():
    user_id = new_uuid()
    registered_at = datetime.now(timezone.utc)
    disabled_at = datetime.now(timezone.utc)
    user = User.register(
        user_id=user_id,
        email=Email("alice@example.com"),
        nickname=Nickname("alice"),
        password_hash=HashedPassword("hash"),
        occurred_at=registered_at,
    )
    user.pull_events()

    user.disable(occurred_at=disabled_at)

    assert user.is_active is False
    assert user.pull_events() == [
        UserDisabled(user_id=user_id, occurred_at=disabled_at)
    ]


def test_user_disable_is_idempotent():
    now = datetime.now(timezone.utc)
    user_id = new_uuid()
    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
                nickname="alice",
                password_hash="hash",
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=now,
            ),
            UserDisabled(user_id=user_id, occurred_at=now),
        ]
    )

    user.disable(occurred_at=now)

    assert user.pull_events() == []


def test_user_register_records_user_registered_event():
    user_id = new_uuid()
    occurred_at = datetime.now(timezone.utc)

    user = User.register(
        user_id=user_id,
        email=Email("alice@example.com"),
        nickname=Nickname("alice"),
        password_hash=HashedPassword("hash"),
        occurred_at=occurred_at,
    )

    events = user.pull_events()
    assert events == [
        UserRegistered(
            user_id=user_id,
            email="alice@example.com",
            nickname="alice",
            password_hash="hash",
            authority=Authority.USER.value,
            is_admin=False,
            is_active=True,
            occurred_at=occurred_at,
        )
    ]
    assert user.pull_events() == []


def test_user_rebuilds_state_from_history():
    user_id = new_uuid()
    occurred_at = datetime.now(timezone.utc)

    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
                nickname="alice",
                password_hash="hash",
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=occurred_at,
            ),
            UserPromotedToAdmin(user_id=user_id, occurred_at=occurred_at),
        ]
    )

    assert user.id == user_id
    assert user.email == Email("alice@example.com")
    assert user.nickname == Nickname("alice")
    assert user.password_hash == HashedPassword("hash")
    assert user.is_admin is True
    assert user.authority is Authority.ADMIN
    assert user.is_active is True
    assert user.version == 2
    assert user.pull_events() == []
