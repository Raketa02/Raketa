"""The audience a token is read under, at the token service itself.

``tests/api/test_club_sessions.py`` drives the fence through both surfaces. What
it cannot reach over HTTP is a **refresh** token from before audiences: one is
only useful beside the row it was stored with, and that row's hash is of the
original string. So the rule — *no audience is a player-app token*
(``docs/adr/0185`` §6) — is asserted here for both kinds of token, against the
real adapter.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.bootstrap.composition import build_clock, build_token_service
from app.core.config import get_settings
from app.modules.auth.domain.audience import Audience


def minted_before_audiences(token_type: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "token_type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "iss": settings.JWT_ISSUER,
            "jti": uuid.uuid4().hex,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


@pytest.mark.parametrize("token_type", ["access", "refresh"])
def test_a_token_with_no_audience_is_read_as_the_player_app_s(token_type):
    tokens = build_token_service(get_settings(), clock=build_clock())
    decode = getattr(tokens, f"decode_{token_type}")
    old = minted_before_audiences(token_type)

    assert decode(old, audience=Audience.PLAYER_APP)["token_type"] == token_type
    with pytest.raises(jwt.InvalidTokenError):
        decode(old, audience=Audience.CLUB)


@pytest.mark.parametrize("token_type", ["access", "refresh"])
@pytest.mark.parametrize("audience", list(Audience))
def test_a_token_is_read_only_under_the_audience_it_was_issued_for(
    token_type, audience
):
    tokens = build_token_service(get_settings(), clock=build_clock())
    issued = getattr(tokens, f"issue_{token_type}")(
        str(uuid.uuid4()), audience=audience
    ).token
    decode = getattr(tokens, f"decode_{token_type}")

    assert decode(issued, audience=audience)["aud"] == audience.value
    for other in set(Audience) - {audience}:
        with pytest.raises(jwt.InvalidTokenError):
            decode(issued, audience=other)
