"""*Let's play* — the two interest routes.

**A top-level resource, not a sub-resource of a search.** Interest outlives the
search that surfaced it — twenty-one days against a search run once — and a
nested route would say the opposite. The search still travels, as the origin key,
on the body.

**Idempotent per `(from, to, sport)`.** A second yes creates nothing, spends no
cap slot and does not re-date the expiry: a button that says it costs nothing must
not be a way to keep a yes alive for ever. It answers `200` where the first
answered `201`, so a client can tell *that was new* from *that already stood*
without either being an error.

**The one refusal that is about you is the cap**, and it is shown before it bites:
every read carries the outstanding count and the cap in force, because a cap the
player cannot see is a refusal they cannot predict.

**Nobody is told they were declined, and nobody is told they were passed over.**
There is no route here through which a one-sided yes reaches its recipient, and
no shape in which a refusal reaches its subject. The only thing that crosses about
somebody else is a **mutual** — and it crosses only to a person who said yes
first.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.matchmaking.application.commands import (
    ExpressInterestCommand,
    ReadInterestCommand,
)
from app.modules.matchmaking.application.express_interest import ExpressedInterest
from app.modules.matchmaking.application.read_interest import InterestSummary
from app.modules.matchmaking.domain.interest import Interest, OutstandingCount
from app.modules.matchmaking.presentation.dependencies import (
    ExpressInterestDep,
    ReadInterestDep,
)
from app.modules.matchmaking.presentation.interest_schemas import (
    ExpressedInterestResponse,
    ExpressInterestRequest,
    InterestListResponse,
    OutgoingInterestSchema,
    OutstandingSchema,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/interest", tags=["interest"])


@router.post(
    "",
    response_model=ExpressedInterestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": (
                "The yes stands, and it is new. It lapses at `expires_at`, "
                "which was dated the moment it was created."
            ),
        },
        status.HTTP_200_OK: {
            "model": ExpressedInterestResponse,
            "description": (
                "You had already said this. **Nothing was created and nothing "
                "was extended** — the yes comes back with the expiry it was "
                "born with."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`origin_search_not_found` — no search of **yours** showed that "
                "player for that sport. The origin key is refused rather than "
                "linked as null.\n\n"
                "`outstanding_interest_cap_reached` — you already have the most "
                "yeses in flight this sport allows. **Nothing of yours is "
                "shortened to make room**; wait, or one of them comes back. The "
                "count and the cap are on `GET /api/v1/interest`."
            ),
        },
    },
    summary="Let's play",
    description=(
        "One tap, costing nothing — and it actually does something: you rise in "
        "that player's next search for this sport, **with the reason printed**, "
        "so the lift is never mistaken for a match.\n\n"
        "**Nobody is notified.** A one-sided yes is silent and stays silent. It "
        "becomes visible only when the other person goes looking for a game.\n\n"
        "**`search_id` is required.** It says which search surfaced this person "
        "— a yes citing a search that is unknown, that is somebody else's or "
        "that never showed them is refused, never recorded with an empty "
        "link.\n\n"
        "**Idempotent.** Tapping again returns the same yes with the same "
        "expiry, at `200`.\n\n"
        "**It lapses.** Every yes carries its own `expires_at`; when it passes "
        "the yes is simply gone, and that person may be dealt to you again. "
        "**Never compute the expiry yourself** — the window is ruleset "
        "configuration and does not cross the wire as a number."
    ),
)
async def express_interest(
    payload: ExpressInterestRequest,
    response: Response,
    user: CurrentUserDep,
    use_case: ExpressInterestDep,
) -> ExpressedInterestResponse:
    expressed = await use_case.execute(
        ExpressInterestCommand(
            from_player_id=user.id,
            to_player_id=payload.player_id,
            sport=payload.sport,
            search_id=payload.search_id,
        )
    )
    if not expressed.created:
        # **The second tap is not an error and not a creation.** Set here rather
        # than declared on the route because only the use case knows which of
        # the two happened, and the difference is a fact about the ledger rather
        # than about the request.
        response.status_code = status.HTTP_200_OK
    return _expressed(expressed)


@router.get(
    "",
    response_model=InterestListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Your outgoing yeses, the ones that came back, and where each "
                "sport stands against its cap."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`gate_data_unavailable` — the block set could not be "
                "evaluated, so the list is refused rather than served "
                "unverified."
            ),
        },
    },
    summary="Your Let's play yeses",
    description=(
        "**Outgoing and mutuals only.** There is no inbox: a yes nobody has "
        "answered stays silent, in both directions, which is what makes saying "
        "yes low-stakes. You are never told that somebody declined you, and you "
        "are never shown who said yes to you unless you said it back.\n\n"
        "**Every outgoing row carries its own `expires_at`**, so the screen can "
        "show what is still live without knowing the window.\n\n"
        "**`outstanding` carries the count, the cap and `ttl_days` for every "
        "sport**, before you are near either — a cap you cannot see is a "
        "refusal you cannot predict, and how long a yes lives is the number the "
        "deck's ending prints. Render these; never hardcode the numbers."
    ),
)
async def read_interest(
    user: CurrentUserDep,
    use_case: ReadInterestDep,
) -> InterestListResponse:
    summary = await use_case.execute(ReadInterestCommand(player_id=user.id))
    return _summary(summary)


def _expressed(expressed: ExpressedInterest) -> ExpressedInterestResponse:
    return ExpressedInterestResponse(
        interest=_row(expressed.interest),
        mutual=expressed.mutual,
        outstanding=_count(expressed.outstanding),
        challenge_id=expressed.challenge_id,
    )


def _summary(summary: InterestSummary) -> InterestListResponse:
    return InterestListResponse(
        outgoing=[_row(row) for row in summary.outgoing],
        mutual=[_row(row) for row in summary.mutual],
        outstanding=[_count(entry) for entry in summary.outstanding],
    )


def _count(entry: OutstandingCount) -> OutstandingSchema:
    """One sport's standing, rendered the one way both routes render it."""

    return OutstandingSchema(
        sport=entry.sport,
        outstanding=entry.outstanding,
        cap=entry.cap,
        ttl_days=entry.ttl_days,
    )


def _row(interest: Interest) -> OutgoingInterestSchema:
    """One yes, as its **sender** is allowed to see it.

    The recipient is a bare id and nothing else: the card, the level and the area
    belong to a search's answer, where a gate decided they may be shown. A yes is
    a fact about what *you* did, and a screen that quietly re-published somebody's
    profile off the back of it would be an inbox with extra steps.
    """

    return OutgoingInterestSchema(
        player_id=interest.to_player_id,
        sport=interest.sport,
        at=interest.at,
        expires_at=interest.expires_at,
    )
