from datetime import datetime, timezone

import pytest

from app.modules.users.domain.errors import InactiveUserCannotBePromoted
from app.modules.users.domain.events import (
    UserDisabled,
    UserNamed,
    UserPromotedToAdmin,
    UserRegistered,
)
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    AdultAttestation,
    Authority,
    Email,
    HashedPassword,
    Name,
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


def test_nickname_refuses_a_space():
    """A nickname is a handle, and a space is not in it (``docs/adr/0171`` §1).

    Pinned beside the name's rule so the two cannot drift together: the name is
    where a space goes, and this is what keeps *Ania Kowalska* out of the field
    that is unique.
    """

    with pytest.raises(ValueError):
        Nickname("ania kowalska")


def test_name_trims_and_collapses_whitespace():
    """The name rule (``docs/adr/0171`` §1): trimmed, runs of whitespace one space.

    Every kind of whitespace, not only the space bar — a name pasted with a tab
    or a line break in it is the same name.
    """

    assert Name("  Ania   Kowalska ").value == "Ania Kowalska"
    assert Name("Diego\t\nFabregat").value == "Diego Fabregat"


def test_name_is_two_to_sixty_four_characters_after_trimming():
    Name("Al")
    Name("x" * 64)
    with pytest.raises(ValueError):
        Name("A")
    with pytest.raises(ValueError):
        Name(" A ")
    with pytest.raises(ValueError):
        Name("x" * 65)
    with pytest.raises(ValueError):
        Name("   ")


def test_name_admits_what_a_nickname_refuses():
    """A space, an apostrophe, an accent: a name is what a person is called."""

    assert Name("O'Neil-Ferrer").value == "O'Neil-Ferrer"
    assert Name("Zoë Núñez").value == "Zoë Núñez"
    assert Name("Diego").value == "Diego"


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
        password_hash=HashedPassword("hash"),
        attestation=AdultAttestation(True),
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
        password_hash=HashedPassword("hash"),
        attestation=AdultAttestation(True),
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
        password_hash=HashedPassword("hash"),
        attestation=AdultAttestation(True),
        occurred_at=occurred_at,
    )

    events = user.pull_events()
    assert events == [
        UserRegistered(
            user_id=user_id,
            email="alice@example.com",
            password_hash="hash",
            authority=Authority.USER.value,
            is_admin=False,
            is_active=True,
            occurred_at=occurred_at,
            adult_attested=True,
        )
    ]
    assert user.pull_events() == []


def test_user_is_registered_unnamed():
    """Sign-up is credentials; a fresh account has no name and no nickname
    (``docs/adr/0171`` §2)."""

    user = User.register(
        user_id=new_uuid(),
        email=Email("alice@example.com"),
        password_hash=HashedPassword("hash"),
        attestation=AdultAttestation(True),
        occurred_at=datetime.now(timezone.utc),
    )

    assert user.name is None
    assert user.nickname is None


def test_the_naming_records_one_event_carrying_both():
    user_id = new_uuid()
    now = datetime.now(timezone.utc)
    user = User.register(
        user_id=user_id,
        email=Email("alice@example.com"),
        password_hash=HashedPassword("hash"),
        attestation=AdultAttestation(True),
        occurred_at=now,
    )
    user.pull_events()

    user.name_as(
        name=Name("  Ania   Kowalska "), nickname=Nickname("ania_k"), occurred_at=now
    )

    assert user.name == Name("Ania Kowalska")
    assert user.nickname == Nickname("ania_k")
    assert user.pull_events() == [
        UserNamed(
            user_id=user_id, name="Ania Kowalska", nickname="ania_k", occurred_at=now
        )
    ]


def test_the_naming_is_repeatable_and_the_fold_keeps_the_latest():
    """A later change is the same act (``docs/adr/0171`` §2)."""

    user_id = new_uuid()
    now = datetime.now(timezone.utc)
    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
                password_hash="hash",
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=now,
            ),
            UserNamed(user_id=user_id, name="Ania", nickname="ania", occurred_at=now),
            UserNamed(
                user_id=user_id,
                name="Ania Kowalska",
                nickname="ania_k",
                occurred_at=now,
            ),
        ]
    )

    assert user.name == Name("Ania Kowalska")
    assert user.nickname == Nickname("ania_k")
    assert user.version == 3


def test_naming_yourself_the_same_way_again_records_nothing():
    """Admitted, and a no-op: the same rule ``disable`` follows for a second
    disable. The stream records acts, and re-submitting an unchanged step is
    not one."""

    user_id = new_uuid()
    now = datetime.now(timezone.utc)
    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
                password_hash="hash",
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=now,
            ),
            UserNamed(user_id=user_id, name="Ania", nickname="ania", occurred_at=now),
        ]
    )

    user.name_as(name=Name(" Ania "), nickname=Nickname("ania"), occurred_at=now)

    assert user.pull_events() == []


def test_user_rebuilds_state_from_history():
    user_id = new_uuid()
    occurred_at = datetime.now(timezone.utc)

    user = User.from_history(
        [
            UserRegistered(
                user_id=user_id,
                email="alice@example.com",
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
    assert user.nickname is None
    assert user.password_hash == HashedPassword("hash")
    assert user.is_admin is True
    assert user.authority is Authority.ADMIN
    assert user.is_active is True
    assert user.version == 2
    assert user.pull_events() == []
