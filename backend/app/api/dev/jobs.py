"""*Run it now*: a timed rule's job, run over what is due at the real *now*
(``docs/adr/0194`` §5; #592). The club's answer window, #591's press, went
with On request (#669).

**It runs the job's own unit of work** — the code the scheduler's loop runs
each tick (``app/bootstrap/jobs.py``) — over this request's session and clock,
which is the real *now*. **It never brings anything forward**: a unit of work
acts only on what is already due, so a press does nothing the next scheduled
tick would not, and work that is not due yet is left exactly as it was. The
state pane's countdowns (``board.py``) say when a press will find something.

A job's path is its name in the logs and on its task, so the press and the
scheduler are one job by one name. **Every job the scheduler registers is
decided about here**: it has a press (``RUN_IT_NOW``), or it is named with the
reason it has none (``NOT_RUN_HERE``) — and
``tests/api/test_games_test_console_time.py`` fails the day a job is registered
that is neither.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession
from app.api.dev.dependencies import (
    AskHowDidItGoDep,
    TheCutOffDep,
    TheHoldingDep,
    DecideClubPayoutsDep,
    DestroyEndedConversationsDep,
    ExpireProposalsDep,
    ProposeGamesDep,
    RunOutTheTimeToPayDep,
    RunOutTheInvitationsDep,
    SettleRatingsOnResultsDep,
    SummariseNewBookingsDep,
)
from app.bootstrap.jobs import (
    CLUB_PAYOUTS_JOB,
    CONVERSATION_SWEEP_JOB,
    CUT_OFF_JOB,
    GET_YOUR_LEVEL_JOB,
    HOLDING_JOB,
    HOW_DID_IT_GO_JOB,
    INVITATIONS_JOB,
    MAIL_DELIVERY_JOB,
    NEW_BOOKINGS_SUMMARY_JOB,
    PHOTO_REVIEW_BACKFILL_JOB,
    PHOTO_SWEEP_JOB,
    PROPOSAL_EXPIRY_JOB,
    PROPOSER_JOB,
    PROPOSER_ON_CHANGES_JOB,
    RATING_CATCH_UP_JOB,
    TIME_TO_PAY_JOB,
    propose_over,
)
from app.modules.clubs.domain.court_hours import DAY_CLOSES

router = APIRouter(prefix="/jobs", tags=["dev"])

#: Every job the new games run, by the name the scheduler runs it under, with
#: what its press is called — in the order the page draws them: a game's life,
#: from its first card to its club's day close and after.
RUN_IT_NOW: Final[Mapping[str, str]] = MappingProxyType(
    {
        PROPOSER_JOB: "the proposer",
        PROPOSAL_EXPIRY_JOB: "the book-by sweep",
        TIME_TO_PAY_JOB: "time to pay",
        INVITATIONS_JOB: "a friend's 24 hours run out",
        HOLDING_JOB: "hold the shares",
        CUT_OFF_JOB: "the cut-off",
        HOW_DID_IT_GO_JOB: "the hour ends · How did it go?",
        CLUB_PAYOUTS_JOB: "the day close · club payouts",
        NEW_BOOKINGS_SUMMARY_JOB: "the day close · new bookings summary",
        RATING_CATCH_UP_JOB: "the rating catch-up",
        CONVERSATION_SWEEP_JOB: "the chat sweep",
    }
)

#: Every other job the scheduler registers, and why it has no press.
NOT_RUN_HERE: Final[Mapping[str, str]] = MappingProxyType(
    {
        PROPOSER_ON_CHANGES_JOB: (
            "The proposer's short tick: the sweep's own batch over the pools a "
            "change this process delivered made due, every five seconds — and "
            "the proposer's press walks every pool, theirs among them."
        ),
        MAIL_DELIVERY_JOB: (
            "Not a timed rule: the mail queue's drain, every two seconds. An "
            "email waits on nothing a press could bring forward."
        ),
        GET_YOUR_LEVEL_JOB: (
            "An account's, not a game's: Get your level, told once to an account "
            "a day after its first group join while rated in nothing (#727)."
        ),
        PHOTO_SWEEP_JOB: "Photos, not games: uploads never committed to a profile.",
        PHOTO_REVIEW_BACKFILL_JOB: (
            "Photos, not games: the reviewer asked about photos nobody asked it about."
        ),
    }
)


class RunItNowJob(BaseModel):
    job: str = Field(
        description="The job's name — its press is `POST /dev/jobs/{job}`."
    )
    title: str = Field(description="What its press is called.")


class NotRunHereJob(BaseModel):
    job: str
    why: str = Field(description="Why the console has no press for it.")


class JobsResponse(BaseModel):
    jobs: list[RunItNowJob] = Field(
        description="Every job the new games run, each with its *Run it now*."
    )
    not_here: list[NotRunHereJob] = Field(
        description="Every other job the scheduler runs, and why it has no press."
    )


class RanResponse(BaseModel):
    job: str = Field(description="The job's name, as the scheduler runs it.")
    done: int = Field(description="What was due, and was done.")
    conflicts: int = Field(
        description="What another process was doing at that moment, stepped over."
    )
    says: str = Field(description="What happened, for the tester.")


def _summary(job: str) -> str:
    return f"Run it now · {RUN_IT_NOW[job]}"


@router.get(
    "",
    response_model=JobsResponse,
    summary="The jobs the console runs now, and the ones it does not",
)
async def read_jobs() -> JobsResponse:
    return JobsResponse(
        jobs=[RunItNowJob(job=job, title=title) for job, title in RUN_IT_NOW.items()],
        not_here=[NotRunHereJob(job=job, why=why) for job, why in NOT_RUN_HERE.items()],
    )


@router.post(
    f"/{PROPOSER_JOB}",
    response_model=RanResponse,
    summary=_summary(PROPOSER_JOB),
    description=(
        "The sweep over every pool: whatever each group's free court hours and "
        "free, fitting members make — a pick dealt, a seat a no left handed to "
        "the next best fits, a pick widened at half In, a card that lost its "
        "court hour recorded so. What a game already holds is dealt nothing "
        "twice. *Fresh deal* is the same for one group."
    ),
)
async def run_the_proposer(db: DbSession, proposer: ProposeGamesDep) -> RanResponse:
    proposed = await propose_over(
        db, proposer, await proposer.every_pool(), job=PROPOSER_JOB
    )
    done = proposed.made + proposed.dealt + proposed.lost + proposed.redealt
    return RanResponse(
        job=PROPOSER_JOB,
        done=done,
        conflicts=proposed.refused,
        says=(
            f"Over {proposed.pools} group(s): {proposed.made} pick(s) made, "
            f"{proposed.dealt} version(s) dealt, {proposed.redealt} cancelled "
            f"game(s) re-dealt, {proposed.lost} card(s) found without their court "
            f"hour."
            if done
            else "Nothing to deal: every group's cards are as the proposer would "
            "leave them."
        ),
    )


@router.post(
    f"/{PROPOSAL_EXPIRY_JOB}",
    response_model=RanResponse,
    summary=_summary(PROPOSAL_EXPIRY_JOB),
    description=(
        "Records every card whose book-by passed unfilled. **The record, not the "
        "fact**: a card is gone from every deck at its book-by whether or not "
        "this has run. A card before its book-by is left filling."
    ),
)
async def run_the_book_by_sweep(expire: ExpireProposalsDep) -> RanResponse:
    expired = await expire.execute()
    return RanResponse(
        job=PROPOSAL_EXPIRY_JOB,
        done=expired.proposals,
        conflicts=expired.conflicts,
        says=(
            f"{expired.proposals} card(s) past their book-by recorded as expired."
            if expired.proposals
            else "No card is past its book-by unrecorded: nothing was done."
        ),
    )


@router.post(
    f"/{TIME_TO_PAY_JOB}",
    response_model=RanResponse,
    summary=_summary(TIME_TO_PAY_JOB),
    description=(
        "Runs out every refused share's time to pay that is up (#625) — and its "
        "time to fix the card, before the cut-off (#638): the payer's seat "
        "reopens — offered to others, theirs to take back while free — and the "
        "holds the others kept are let go. On a booked game whose "
        "holding was refused (#639), the player's seat opens to Fill in as a "
        "leaver's, and they owe nothing. A time still running is left as it "
        "is."
    ),
)
async def run_the_time_to_pay(run_out: RunOutTheTimeToPayDep) -> RanResponse:
    ran_out = await run_out.execute()
    return RanResponse(
        job=TIME_TO_PAY_JOB,
        done=ran_out.games,
        conflicts=ran_out.conflicts,
        says=(
            f"{ran_out.games} game(s) whose time to pay was up: the seat reopened."
            if ran_out.games
            else "No time to pay is up: nothing was done."
        ),
    )


@router.post(
    f"/{INVITATIONS_JOB}",
    response_model=RanResponse,
    summary=_summary(INVITATIONS_JOB),
    description=(
        "Runs out every friends game invitation whose 24 hours ended with no "
        "answer (#751): silence is *Not this time*, and the sender is told "
        "*Ania didn't answer*. An invitation whose time still runs is left as "
        "it is."
    ),
)
async def run_the_invitations(run_out: RunOutTheInvitationsDep) -> RanResponse:
    ran = await run_out.execute()
    return RanResponse(
        job=INVITATIONS_JOB,
        done=ran.ran_out,
        conflicts=ran.conflicts,
        says=(
            f"{ran.ran_out} invitation(s) ran out: the sender is told."
            if ran.ran_out
            else "No invitation's 24 hours are up: nothing was done."
        ),
    )


@router.post(
    f"/{HOLDING_JOB}",
    response_model=RanResponse,
    summary=_summary(HOLDING_JOB),
    description=(
        "At each checked share's Holding time — four days before its game's "
        "cut-off — holds it on its card again, to stay until the cut-off "
        "(#639). A game that filled far ahead had those cards only checked: a "
        "hold made without its player would not have lasted until the cut-off. "
        "A card refused now gives its player thirty minutes to fix it, the game "
        "still booked — run out, their seat opens to Fill in and they owe "
        "nothing. A share whose Holding time is still ahead is left checked."
    ),
)
async def run_the_holding(holding: TheHoldingDep) -> RanResponse:
    ran = await holding.execute()
    done = ran.held + ran.refused
    return RanResponse(
        job=HOLDING_JOB,
        done=done,
        conflicts=ran.conflicts,
        says=(
            f"{ran.held} checked share(s) held until the cut-off; "
            f"{ran.refused} refused, each player given time to fix the card."
            if done
            else "No checked share has reached its Holding time: nothing was done."
        ),
    )


@router.post(
    f"/{CUT_OFF_JOB}",
    response_model=RanResponse,
    summary=_summary(CUT_OFF_JOB),
    description=(
        "Once a booked game's cut-off has come: a full game has every share "
        "held for it taken — the money moves then, and the club's Collected "
        "with it — and a game with a seat open since before its cut-off is "
        "called off, every hold let go so nobody pays anything, the court "
        "free, the club emailed. A game whose cut-off is still ahead is left as "
        "it is, held, seat open or not."
    ),
)
async def run_the_cut_off(cut_off: TheCutOffDep) -> RanResponse:
    ran = await cut_off.execute()
    done = ran.games + ran.taken
    return RanResponse(
        job=CUT_OFF_JOB,
        done=done,
        conflicts=ran.conflicts,
        says=(
            f"{ran.taken} full game(s) had their held shares taken; "
            f"{ran.games} game(s) short at their cut-off called off, every hold "
            "let go."
            if done
            else "No game has a cut-off that has come with anything to do: "
            "nothing was done."
        ),
    )


@router.post(
    f"/{HOW_DID_IT_GO_JOB}",
    response_model=RanResponse,
    summary=_summary(HOW_DID_IT_GO_JOB),
    description=(
        "Asks all four of every Competitive booked game whose hour ended in the "
        "last half hour *How did it go?* (#663) — once, given at the hour's "
        "end — while nobody has put a score up and nobody Didn't come. A For "
        "fun game asks nobody, and a game whose hour is still running is left "
        "as it is."
    ),
)
async def run_how_did_it_go(ask: AskHowDidItGoDep) -> RanResponse:
    asked = await ask.execute()
    return RanResponse(
        job=HOW_DID_IT_GO_JOB,
        done=asked.games,
        conflicts=asked.conflicts,
        says=(
            f"{asked.games} game(s) whose hour ended: its players asked How did it go?"
            if asked.games
            else "No game's hour ended with anybody left to ask: nothing was done."
        ),
    )


@router.post(
    f"/{CLUB_PAYOUTS_JOB}",
    response_model=RanResponse,
    summary=_summary(CLUB_PAYOUTS_JOB),
    description=(
        f"At the close of the last club day — {DAY_CLOSES}:00 in Kraków — decides each "
        "club's payout of what its games over by then left it, once their money "
        "is settled; the outbox then pays it out and emails the desk. A game of "
        "a day still open waits for that day's close, and a club paid for the "
        "day already waits for the next."
    ),
)
async def run_the_club_payouts(decide: DecideClubPayoutsDep) -> RanResponse:
    decided = await decide.execute()
    return RanResponse(
        job=CLUB_PAYOUTS_JOB,
        done=decided.decided,
        conflicts=decided.conflicts,
        says=(
            f"{decided.decided} club payout(s) decided: the outbox pays them out "
            f"and tells each desk."
            if decided.decided
            else "No club is owed anything a closed day settled: nothing was done."
        ),
    )


@router.post(
    f"/{NEW_BOOKINGS_SUMMARY_JOB}",
    response_model=RanResponse,
    summary=_summary(NEW_BOOKINGS_SUMMARY_JOB),
    description=(
        "At the close of the last club day, emails each club's desk the games "
        "booked at it that day — once a day, and nothing on a day nothing was "
        "booked. A day still open is summed up at its close."
    ),
)
async def run_the_new_bookings_summary(
    summarise: SummariseNewBookingsDep,
) -> RanResponse:
    summed = await summarise.execute()
    return RanResponse(
        job=NEW_BOOKINGS_SUMMARY_JOB,
        done=summed.clubs,
        conflicts=summed.conflicts,
        says=(
            f"{summed.clubs} desk(s) emailed the closed day's new bookings."
            if summed.clubs
            else "No desk is owed the closed day's new bookings: nothing was done."
        ),
    )


@router.post(
    f"/{RATING_CATCH_UP_JOB}",
    response_model=RanResponse,
    summary=_summary(RATING_CATCH_UP_JOB),
    description=(
        "Settles for rating everything that has become final and nothing has "
        "applied yet: a score silence settled, two scores naming the same winner "
        "settled with the closer, and an agreement the outbox has not delivered "
        "yet. A result still waiting for its answer is not final, and a "
        "disputed one never is — neither moves anything."
    ),
)
async def run_the_rating_catch_up(settle: SettleRatingsOnResultsDep) -> RanResponse:
    settled = await settle.execute()
    return RanResponse(
        job=RATING_CATCH_UP_JOB,
        done=settled.games,
        conflicts=settled.conflicts,
        says=(
            f"{settled.games} confirmed result(s) folded: {settled.ratings} "
            f"Level(s) moved."
            if settled.games
            else "No confirmed result is waiting to move a Level: nothing was done."
        ),
    )


@router.post(
    f"/{CONVERSATION_SWEEP_JOB}",
    response_model=RanResponse,
    summary=_summary(CONVERSATION_SWEEP_JOB),
    description=(
        "Destroys every chat whose game is over and whose grace has run out — "
        "destroyed, not delisted. Every read already hides a chat past its end; "
        "a chat still open is left."
    ),
)
async def run_the_chat_sweep(sweep: DestroyEndedConversationsDep) -> RanResponse:
    swept = await sweep.execute()
    return RanResponse(
        job=CONVERSATION_SWEEP_JOB,
        done=swept.destroyed,
        conflicts=0,
        says=(
            f"{swept.destroyed} of {swept.walked} chat(s) past their end destroyed."
            if swept.destroyed
            else f"None of {swept.walked} chat(s) is past its end: nothing was done."
        ),
    )
