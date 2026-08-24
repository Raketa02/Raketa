"""`PUT /api/v1/push/device` — where one phone can be reached.

The push channel's whole wire surface, and there is deliberately nothing else on
it. A notification is *a prompt to look* (ADR-0062): nothing about it is
requested, acknowledged, listed or dismissed by a client, so the only thing a
phone ever tells the server is where it is.

**It lives in ``now/``** although its path says ``push``, for the reason the
departure and result routes live there while their paths say ``matches``: the
channel exists to carry the offers region's own seats, everything it composes
from is Now's, and putting it elsewhere would make a second context import Now
to answer a question about a lock screen.

**`PUT`, because the address of one phone is a thing that is *set*.** The same
phone re-registers on every sign-in, on every token rotation and whenever its
settings change, and each of those is *this is where I am now* rather than *here
is one more device*. The key is the token, so a client with a stale token and a
fresh one registers two phones — which is the truth, and is what the send's
per-device loop is for.

**204 and no body.** ADR-0074 has every action *off Now* hand back Now's update
so the screen corrects itself; registering a token is not an act off Now, moves
no card, and has nothing to say back.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.modules.now.application.push import RegisterDeviceCommand
from app.modules.now.presentation.dependencies import RegisterDeviceDep
from app.modules.now.presentation.push_schemas import RegisterDeviceRequest
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/push", tags=["push"])


@router.put(
    "/device",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Register this phone for seat notifications",
)
async def register_device(
    current_user: CurrentUserDep,
    use_case: RegisterDeviceDep,
    body: RegisterDeviceRequest,
) -> None:
    """Record where this player can be reached, replacing what this phone said.

    **The player is the token's holder and never a field on the request.** A
    body naming a player would let one account point the channel at another
    account's phone, which is the one failure in this channel worse than
    silence — and it is why registering a token also takes it off every *other*
    player, since a phone that has been signed out of still answers to it.

    Nothing here can be refused: any player may be reachable, the token is
    opaque to us, and all three ``timeSensitiveSetting`` values are equally
    acceptable because none of them changes what the server does.
    """

    await use_case.execute(
        RegisterDeviceCommand(
            player_id=current_user.id,
            token=body.token,
            platform=body.platform,
            time_sensitive=body.time_sensitive_setting,
        )
    )
