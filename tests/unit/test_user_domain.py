import pytest

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
    user = User(
        id=new_uuid(),
        email=Email("a@b.com"),
        nickname=Nickname("alice"),
        password_hash=HashedPassword("hash"),
    )
    assert user.authority is Authority.USER and not user.is_admin
    user.promote_to_admin()
    assert user.authority is Authority.ADMIN and user.is_admin
