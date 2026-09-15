"""*Who among these people chose a friendly, in this sport?* — the one thing the
mutual mint borrows about a person's **declaration**.

**A mutual's game is counted unless either declared *for fun***
(``docs/adr/0169`` §8). The deck reads no declaration — every deal runs on the
fun ruler for everybody, and a competitive declaration moves nobody on it — but
the game a mutual opens is somebody's evening, and a wish they stated for the
sport is honoured there: the mint reads both declarations and stamps the
challenge ``FOR_FUN`` when either said so, otherwise leaves the mode absent and
the existing derivation — *a friendly is a thing people choose* — makes the
game counted.

**It is here rather than on ``ports.py`` on the games seams' pattern**
(``planned_game.py``, ``settled_game.py``, ``seatable_game.py``): an outward
read on another context's own record, made by exactly one caller, kept in a
file named for the question so the seam is findable. ``ports.py`` does hold
borrowed facts about people — a handle, a hold — but each of those is read by
a screen of this context's own; this one is read by the mint alone, and the
nearer alternative, ``court_safety.py`` reading ``player_profile``'s repository
directly, was declined because the issue asks for a port in this context's
words. What ``player_profile`` owns is what somebody *declared*, kept per
``(player, sport)`` (``docs/adr/0094``); what crosses is one word — *chose a
friendly* — and the three-valued declaration behind it does not:
``COMPETITIVE``, ``NO_PREFERENCE`` and *never declared* are three different
facts to that context and one absence to this rule, and a port that handed the
enum over would be handing a caller the means to tell them apart and,
eventually, a reason to. The adapter (``infrastructure/profile_friendly_choice.py``)
is where the two vocabularies meet.

**Declared in this context's own words, and never read through the matcher.**
The fill already resolves a mode from a declaration on the matcher's side
(``matchmaking/domain/deck.py``'s ``mode_for_intent``), and it would be one
import away — but the arrow runs ``matchmaking -> challenges`` and never back
(``.importlinter``), and that mapping answers a different question anyway: which
*weight vector* a search runs under, where ``NO_PREFERENCE`` inherits the fun
ruler. Here ``NO_PREFERENCE`` chooses nothing, because the rule is about a wish
somebody stated and indifference is not one.

**Only the mutual mint reads it, and the send deliberately does not.** A send
carries the mode its search ran under — the organiser picked a tab — and the
fill inherits the challenge's; neither has a declaration to honour that the
surface did not already ask about.
"""

from __future__ import annotations

from typing import Collection, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Sport


@runtime_checkable
class FriendlyChoiceQuery(Protocol):
    """*Which of these people chose a friendly in this sport?*

    Signed by an adapter that reads ``player_profile``'s own declaration
    repository, wired in the composition root with every other choice of
    implementation.
    """

    async def chose_a_friendly_among(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> frozenset[UUID]:
        """The subset of these players whose standing declaration for this sport
        is *for fun*.

        **Per sport, because the declaration is** (``docs/adr/0094``): a padel
        *for fun* says nothing about a tennis game between the same two people,
        and the mint asks in the sport the yes was said in.

        **Absence is one absence.** A player who declared *competitive*, one who
        declared *no preference* and one who never declared are all simply not
        in the answer — the rule has two outcomes and none of those three is the
        first. A caller may not learn which it was, and nothing on this port lets
        it ask.

        **Bulk, over the pair, and the shape is what is promised.** The mint has
        exactly two people and always will; the set shape is what every read in
        this codebase takes, and what an implementation does behind it — today's
        walks the pair through the repository's per-pair load — is its own
        business. A caller may never loop instead.

        **What it may not do is answer emptily when it could not tell.** A read
        that cannot complete raises what it raised, and the mint it was part of
        fails with it inside the transaction of the yes that caused it, writing
        nothing — ``OpenChallengeQuery``'s posture rather than
        ``SettledGameQuery``'s, and for a reason: an empty answer here reads as
        *nobody chose a friendly* and mints a **counted** game on the strength
        of a fact this call does not have, which is the exact evening somebody
        may have said they did not want. The declaration lives in the same
        event store the challenge is about to be written to, so a store that
        cannot answer this is one the mint could not have written to either.
        """
        ...


__all__ = ["FriendlyChoiceQuery"]
