from datetime import datetime, timedelta, timezone

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
