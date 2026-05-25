from datetime import datetime, timedelta, timezone

from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)
from app.modules.auth.domain.refresh_token import RefreshToken
from app.shared.ids import new_uuid


def _token(expires_at):
    return RefreshToken(
        id=new_uuid(),
        user_id=new_uuid(),
        token_hash="hash",
        jti="jti-1",
        refresh_expires_at=expires_at,
    )


def test_is_expired_true_when_past_now():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert _token(past).is_expired(now=datetime.now(timezone.utc)) is True


def test_is_expired_false_when_future():
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    assert _token(future).is_expired(now=datetime.now(timezone.utc)) is False


def test_is_expired_treats_naive_exp_as_utc():
    naive = datetime.utcnow() - timedelta(minutes=1)
    assert _token(naive).is_expired(now=datetime.now(timezone.utc)) is True


def test_revoke_flips_state():
    tok = _token(datetime.now(timezone.utc) + timedelta(hours=1))
    now = datetime.now(timezone.utc)
    tok.revoke(now=now)
    assert tok.is_valid is False
    assert tok.revoked_at == now


def test_issue_records_refresh_token_issued_event():
    token_id = new_uuid()
    user_id = new_uuid()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    occurred_at = datetime.now(timezone.utc)

    tok = RefreshToken.issue(
        token_id=token_id,
        user_id=user_id,
        token_hash="hash",
        jti="jti-1",
        refresh_expires_at=expires_at,
        occurred_at=occurred_at,
    )

    assert tok.pull_events() == [
        RefreshTokenIssued(
            token_id=token_id,
            user_id=user_id,
            jti="jti-1",
            expires_at=expires_at,
            occurred_at=occurred_at,
        )
    ]


def test_revoke_records_refresh_token_revoked_event():
    tok = _token(datetime.now(timezone.utc) + timedelta(hours=1))
    now = datetime.now(timezone.utc)

    tok.revoke(now=now, reason="logout")

    assert tok.pull_events() == [
        RefreshTokenRevoked(
            token_id=tok.id,
            user_id=tok.user_id,
            jti=tok.jti,
            reason="logout",
            occurred_at=now,
        )
    ]


def test_rotate_to_records_refresh_token_rotated_event():
    old = _token(datetime.now(timezone.utc) + timedelta(hours=1))
    new = _token(datetime.now(timezone.utc) + timedelta(hours=1))
    now = datetime.now(timezone.utc)

    old.rotate_to(new, now=now)

    assert old.is_valid is False
    assert old.revoked_at == now
    assert old.pull_events() == [
        RefreshTokenRotated(
            user_id=old.user_id,
            revoked_token_id=old.id,
            revoked_jti=old.jti,
            issued_token_id=new.id,
            issued_jti=new.jti,
            occurred_at=now,
        )
    ]
