"""A challenge born of two yeses that met. **Inline, and it mints nothing when
it cannot.**

*Let's play* is one tap costing nothing, and when the second one lands the two
people have an open game together. The product says so immediately rather than
through a poller: *that player has left the deck for good, because you now have
an open game together* is a promise about what somebody will never see again, and
a promise like that should not depend on a worker running.

**It runs the same safety checks the send runs**, and this is the ticket's
finding rather than a symmetry for its own sake. ``resolve_origin`` has **no
freshness bound** — a search record is immutable and never expires, and the store
will happily find any search of yours, ever — so a *Let's play* can cite a
month-old deck deal. Two month-old yeses with a block taken since would otherwise
walk a challenge past every gate in the product, minted inline, with nobody
looking.

**It asks two questions where the send asks one, and that is what makes it
strictly stricter** (``docs/adr/0152``). The send's question — *are these two
still arranging a game* — releases the moment a line-up completes, and a
**singles** mutual is a completed line-up the instant it exists, both seats
accepted from birth. So the pair rule alone cannot police this path:
``express_interest`` mints on the **mutual** rather than on whether this tap
wrote a row, so every repeat tap of a button that says it costs nothing would
open another challenge, another game and another result window between the same
two people.

What is asked beside it is the mint's own **idempotence** key: *has a mutual
between these two, in this sport, already minted a game that is not finished
with?* Both must pass. Keeping them apart is the whole of ``docs/adr/0152`` §1 —
*are these two already arranging* is a question about a **state** and *has this
act already been performed* is a question about an **act**, and they have
different natural endings. Answering the second with the first is what gave this
path a guard that never released: a mutual-born challenge has every seat accepted
at birth, so *does a challenge still stand between them* answered yes for the
life of the database, in every sport, for ever.

**And the release is a fact about a game, so it is read from ``games``.**
*Finished with* means the mutual-born challenge never became a game, or the game
it became has **settled** — including a ghost, because an entry window that
closed on silence is as final as a confirmed score and two people whose game
evaporated may try again. The send does not get this hold and that is a decision
rather than an omission (``docs/adr/0152`` §5): a send is somebody deliberately
choosing a court, and holding them on an unplayed game would put back the block
#343 argued out.

**A refusal writes nothing, and that is still its whole effect on the log.**
There is no organiser standing at a screen and no press to refuse: the yes
stands, the mutual is still a mutual, and no challenge is opened. That is why
this returns ``None`` rather than raising — a raise would roll back the yes,
which was somebody's own act and is not the thing being refused.

**But a refusal is no longer silence** (``docs/adr/0154``). What this answers
with is *the game these two have*, not *what this call minted*: a repeat tap
held by the idempotence key is answered with the game that key is holding it on,
because the id is already in the guard's hand and discarding it is what left a
pair told *you both said yes* with nothing behind it. ``None`` is kept for the
two cases where there is nothing to name — a game still being **arranged**, and
a gate that refused or could not be read — and those are folded on purpose:
an absence that meant only *a gate refused* would be the trace ``docs/adr/0095``
guarantees a block never leaves.

**It does not commit.** The mint and the yes that caused it are one transaction
(``docs/adr/0003``'s outbox is deliberately not used here), so the transaction
boundary stays a decision about the *command* and the caller owns it.

**And in a singles sport it opens the game too.** Both seats are accepted from
birth, so a two-seat court is ``ON`` the instant it is minted and **no accept
ever happens on it** — the branch in ``AcceptSeat`` that opens a game would never
run, and a tennis game born of two yeses would leave no record that it was ever
arranged. The line-up completing is the trigger, not the tapping, so it is
checked wherever a line-up can complete; in a doubles sport this challenge is
half a game and the accept path takes it from here.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.challenges.application.completed_line_up import hand_over
from app.modules.challenges.application.commands import (
    OpenFromMutualInterestCommand,
)
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import TheGatesCouldNotBeEvaluated
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    OpenChallengeQuery,
)
from app.modules.challenges.domain.settled_game import SettledGameQuery
from app.modules.challenges.domain.standing import Standing
from app.shared.ids import new_uuid


@final
class OpenChallengeFromMutualInterest:
    """Two yeses, one challenge — or nothing at all, silently."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        open_challenges: OpenChallengeQuery,
        settled_games: SettledGameQuery,
        safety: CourtSafety,
        clock: Clock,
        planned_games: PlannedGameHandover,
    ) -> None:
        self._challenges = challenges
        self._open_challenges = open_challenges
        self._settled_games = settled_games
        self._safety = safety
        self._clock = clock
        self._planned_games = planned_games

    async def execute(self, command: OpenFromMutualInterestCommand) -> UUID | None:
        """**The game these two have**, or ``None`` when there is none to name.

        Not *what this call minted* (``docs/adr/0154`` §1). A repeat tap on a
        pair whose mutual has already minted an unfinished game is answered with
        **that** game, because the guard is holding them on it and has its id in
        its hand — and discarding it is what left the pair told *you both said
        yes* with nothing behind it.

        ``None`` covers two unrelated things and may not be narrowed to one
        (§3): the pair have a game **still being arranged**, and a gate
        **refused or could not be read**. The first is innocent and already on
        their own inbox; the second is what 0095 says leaves no trace anywhere
        in any response. Folding them is why this may cross the wire at all.
        """

        at = instant(self._clock.now())
        pair = frozenset({command.player_id, command.other_player_id})
        try:
            admitted = await self._safety.admits(pair)
        except TheGatesCouldNotBeEvaluated:
            return None
        if not admitted:
            return None
        if await self._open_challenges.open_pairs_among(pair, now=at):
            # **The send's own question, asked here deliberately** (``docs/adr/
            # 0152`` §2). Two people with a challenge they are still arranging —
            # a court one of them sent, or a half-built doubles one a mutual
            # minted — must not be given a second one; the guard below cannot
            # catch that, because it is a question about an *act* and this is a
            # question about a *state*. Today's shape used to catch it by
            # reading a superset, which is how the two came to be confused.
            return None

        minted = await self._open_challenges.mutual_born_challenges_that_became_games(
            command.player_id,
            command.other_player_id,
            sport=command.sport,
            now=at,
        )
        if minted:
            # **Nothing minted is nothing to ask about**, which is what this
            # branch is: with no id to ask about the read is not made at all.
            # Asking would let an outage in ``games`` refuse every first mint on
            # the platform — two people with nothing between them held apart by
            # a fact about a game neither of them has.
            try:
                settled = await self._settled_games.settled_among(minted, now=at)
            except Exception:
                # **A read that cannot answer means *no*, and it may not
                # escape.** This runs inside ``express_interest``'s transaction
                # and a raise would roll back the player's yes — somebody's own
                # act, and not the thing being refused. So it fails closed
                # exactly as an unevaluable safety gate does: no game, ``None``,
                # silently, and **nothing named** — a game cannot be named out
                # of a fact this call does not have.
                #
                # **Failing closed is only defensible because a repeat tap
                # retries** (``docs/adr/0152`` §6). The mint hanging off the
                # mutual rather than off *did this tap write a row* is what
                # turns a transient read failure into a delay instead of a game
                # two people never get, and that property is therefore not
                # available to be traded away for simplicity later.
                #
                # It catches broadly for ``CourtSafety._read``'s reason: a
                # provider that raises and a provider that answers something
                # malformed are the same event to a guard — it could not be
                # evaluated — and narrowing this to what today's adapter happens
                # to raise would let the next one fail open.
                return None
            unfinished = tuple(one for one in minted if one not in settled)
            if unfinished:
                # **One mutual mints one game.** *Let's play* is a tap that
                # costs nothing and ``express_interest`` mints on the **mutual**
                # rather than on whether this tap wrote a row — deliberately,
                # because a repeat tap is the one occasion the platform ever
                # gets to retry a mint a gate refused. So the second tap has to
                # be refused here, and it is refused until the game the first
                # one minted is finished with: settled, ghost included. A
                # refused mint writes nothing, so the retry still works.
                #
                # **And it is answered with the game it is holding them on**
                # (``docs/adr/0154`` §1). The newest, which is the one this pair
                # would mean by *our game*; there is one unless a restore or a
                # race left two, and the port orders so that *newest* is a fact
                # rather than set iteration order.
                return unfinished[0]

        challenge = Challenge.opened_from_mutual_interest(
            challenge_id=new_uuid(),
            sport=command.sport,
            organiser_id=command.player_id,
            other_player_id=command.other_player_id,
            occurred_at=at,
        )
        await self._challenges.save(challenge)
        if challenge.standing_at(at) is Standing.ON:
            # A singles court is complete the moment it exists, and nobody will
            # ever tap accept on it — so this is the only place its arrangement
            # can be handed over. A doubles one is half a game and the accept
            # path takes it from here.
            await hand_over(challenge, at=at, games=self._planned_games)
        return challenge.id
