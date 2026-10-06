"""The administrator's official-group routes: create one, list yours, open one,
answer its requests and save its settings (#509, ``docs/adr/0184`` §8).

Mounted on the player surface (``app/api/v1/player.py``), because the
administrator profile runs under the player app's audience
(``docs/adr/0185`` §6), and hung under
``/administrator/clubs/{club_id}/groups`` so that **every route passes the
administrator guard** for the club its own path names — a removal takes effect
on the next request, as ``403 not_an_administrator``.

**There is no route that deletes an official group or leaves one**: running
one is not membership, and only the club moves it (``docs/adr/0183`` §7–§8).

Beside them, under ``/administrator/clubs/{club_id}/handovers``, the one route
that says the Administrator was told the club handed them a group
(``docs/adr/0192``).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import SettingsDep
from app.core.exception_handlers import ErrorResponse
from app.modules.groups.application.commands import (
    AnswerAsAdministratorCommand,
    ChangeOfficialGroupSettingsCommand,
    CreateOfficialGroupCommand,
    NoteHandoversSeenCommand,
)
from app.modules.groups.presentation.dependencies import (
    AdministeringDep,
    ApproveAsAdministratorDep,
    ChangeOfficialGroupSettingsDep,
    CreateOfficialGroupDep,
    DeclineAsAdministratorDep,
    NoteHandoversSeenDep,
    ReadAdministeredGroupDep,
    ReadAdministeredGroupsDep,
)
from app.modules.groups.presentation.schemas import (
    AdministeredGroupResponse,
    AdministeredGroupsResponse,
    CreateOfficialGroupRequest,
    HandoversSeenRequest,
    OfficialGroupSettingsRequest,
    SavedSettingsResponse,
)

router = APIRouter(
    prefix="/administrator/clubs/{club_id}/groups", tags=["administrator"]
)
handovers_router = APIRouter(
    prefix="/administrator/clubs/{club_id}/handovers", tags=["administrator"]
)

_GUARDED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_an_administrator` — this account holds no active "
            "administratorship at that club: removed since the last request, "
            "or never. **Every administrator operation answers this the same "
            "way.**"
        ),
    },
}

_THEIRS: dict[int | str, dict[str, Any]] = {
    **_GUARDED,
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`group_not_found` — **one code for every group that is not "
            "theirs**: no such group, a player group, one at another club, or "
            "one a colleague runs."
        ),
    },
}

#: What an official group's four fields are refused with, in the form's order.
_FIELD_REFUSALS = (
    "A field to correct, named by `details.field`, checked in the form's "
    "order: `group_name_invalid` (`name`) — 1–40 characters once trimmed; "
    "`whatsapp_size_invalid` (`whatsapp_size`) — a whole number from 2 to 1024; "
    "`group_sports_required` (`sports`) — at least one; "
    "`sport_not_offered_by_club` (`sports`, with `details.sport`) — only the "
    "club's. Nothing was recorded."
)

@router.post(
    "",
    response_model=AdministeredGroupResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    responses={
        **_GUARDED,
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": _FIELD_REFUSALS,
        },
    },
    summary="Create an official group for my club",
    description=(
        "One per WhatsApp group the administrator runs. **Its home club is the "
        "club in the path**, fixed. **It has no Owner and nobody in it**: "
        "running it is not membership — an administrator who plays joins it "
        "from their player profile, directly. It gets its link, which never "
        "changes. Answers the group as its administrator's page reads it."
    ),
)
async def create_official_group(
    club_id: UUID,
    payload: CreateOfficialGroupRequest,
    administering: AdministeringDep,
    create: CreateOfficialGroupDep,
    read: ReadAdministeredGroupDep,
    settings: SettingsDep,
) -> AdministeredGroupResponse:
    group_id = await create.execute(
        CreateOfficialGroupCommand(
            administering=administering,
            name=payload.name,
            join_policy=payload.join_policy,
            whatsapp_size=payload.whatsapp_size,
            sports=payload.sports,
        )
    )
    page = await read.execute(group_id, administering=administering)
    return AdministeredGroupResponse.from_view(
        page, public_site=settings.PUBLIC_SITE_URL
    )


@router.get(
    "",
    response_model=AdministeredGroupsResponse,
    status_code=status.HTTP_200_OK,
    responses=_GUARDED,
    summary="The official groups I run at my club",
    description=(
        "The administrator's Groups tab: each group's monogram, name, declared "
        "sports, member count, waiting count and home club, newest created "
        "first — and the club, whose sports are what a group may declare."
    ),
)
async def administered_groups(
    club_id: UUID, administering: AdministeringDep, read: ReadAdministeredGroupsDep
) -> AdministeredGroupsResponse:
    return AdministeredGroupsResponse.from_view(await read.execute(administering))


@router.get(
    "/{group_id}",
    response_model=AdministeredGroupResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses=_THEIRS,
    summary="An official group I run",
    description=(
        "Its link to post, how many players it has, every player newest first "
        "with the day they joined, everybody waiting with every sport they are "
        "rated in and its Level — and its settings: name, who can join, "
        "WhatsApp group size and sports."
    ),
)
async def administered_group(
    club_id: UUID,
    group_id: UUID,
    administering: AdministeringDep,
    read: ReadAdministeredGroupDep,
    settings: SettingsDep,
) -> AdministeredGroupResponse:
    page = await read.execute(group_id, administering=administering)
    return AdministeredGroupResponse.from_view(
        page, public_site=settings.PUBLIC_SITE_URL
    )


@router.put(
    "/{group_id}/settings",
    response_model=SavedSettingsResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        **_THEIRS,
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": _FIELD_REFUSALS,
        },
    },
    summary="Save an official group's settings",
    description=(
        "All four as the settings screen holds them, recorded together or not "
        "at all; saving what the group already says records nothing. **The "
        "link never changes.** **Switching to `ANYONE` admits everybody waiting "
        "at once**, and `admitted` says who."
    ),
)
async def save_settings(
    club_id: UUID,
    group_id: UUID,
    payload: OfficialGroupSettingsRequest,
    administering: AdministeringDep,
    change: ChangeOfficialGroupSettingsDep,
    settings: SettingsDep,
) -> SavedSettingsResponse:
    saved = await change.execute(
        ChangeOfficialGroupSettingsCommand(
            administering=administering,
            group_id=group_id,
            name=payload.name,
            join_policy=payload.join_policy,
            whatsapp_size=payload.whatsapp_size,
            sports=payload.sports,
        )
    )
    return SavedSettingsResponse.from_view(saved, public_site=settings.PUBLIC_SITE_URL)


@router.post(
    "/{group_id}/requests/{player_id}/approve",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **_GUARDED,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — not a group this administrator runs. "
                "`join_request_not_found` — the player has no request waiting: "
                "it was declined, or never made, and nobody is admitted who did "
                "not ask. Nothing was recorded."
            ),
        },
    },
    summary="Approve a Join request on an official group I run",
    description=(
        "The player is a Group member **at once**. Approving somebody already "
        "in changes nothing."
    ),
)
async def approve_join_request(
    club_id: UUID,
    group_id: UUID,
    player_id: UUID,
    administering: AdministeringDep,
    approve: ApproveAsAdministratorDep,
) -> None:
    await approve.execute(
        AnswerAsAdministratorCommand(
            administering=administering, group_id=group_id, player_id=player_id
        )
    )


@router.post(
    "/{group_id}/requests/{player_id}/decline",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_THEIRS,
    summary="Decline a Join request on an official group I run",
    description=(
        "The request is gone **silently**: nothing tells the player, and they "
        "may ask again. Declining a request that is not waiting changes "
        "nothing, and never removes a member."
    ),
)
async def decline_join_request(
    club_id: UUID,
    group_id: UUID,
    player_id: UUID,
    administering: AdministeringDep,
    decline: DeclineAsAdministratorDep,
) -> None:
    await decline.execute(
        AnswerAsAdministratorCommand(
            administering=administering, group_id=group_id, player_id=player_id
        )
    )


@handovers_router.post(
    "/seen",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_GUARDED,
    summary="I was told the club handed me these groups",
    description=(
        "The sheet that says *[club] made you the administrator of [group]* was "
        "closed or followed: each named group this administratorship runs and "
        "has not been told about leaves `/users/me`'s `profiles.handovers`, for "
        "every phone. **Anything else is stepped over, never refused** — a group "
        "handed on meanwhile, told about already, or not theirs."
    ),
)
async def handovers_seen(
    club_id: UUID,
    payload: HandoversSeenRequest,
    administering: AdministeringDep,
    note: NoteHandoversSeenDep,
) -> None:
    await note.execute(
        NoteHandoversSeenCommand(
            administering=administering, group_ids=payload.group_ids
        )
    )
