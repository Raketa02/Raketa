"""Play intent: three values, declared per sport, and never the search's mode.

``docs/adr/0094`` settles it. *A level is proved, never declared*
(``../../../../CONTEXT.md``) and this is the one preference the platform does
take a player's word for — because there is no true answer to check it against
and misdeclaring it costs only the declarer an evening. A sandbagger farms wins;
somebody who says *For fun* and meant it competitively has wasted their own
Tuesday.

**``PlayIntent`` and ``SearchMode`` are two types and never one.** Mode is the
search's setting — which tab you are on, right now, two values. Intent is the
player's declaration — three values. The arities differ, so the most likely bug
in the matcher is a type error rather than a paragraph in a document. There is
no ``SearchMode`` in this repository yet; when it arrives it belongs to the
matcher and not to this module, and the reason to write that down here is that
this is the file somebody would otherwise add it to.

**``NO_PREFERENCE`` is an explicit answer and nobody is ever backfilled to it.**
The matcher cannot otherwise tell *either suits me* from *I never opened that
screen*, and those are different facts — the same shape ``PREFER_NOT_TO_SAY``
has in ``gender.py``, for the same reason.

**Intent is never read as a tag and a tag is never read as intent.** A tag is
*why you are here at all*; intent is *what tonight's game is*, and somebody
tagged ``HERE_TO_COMPETE`` who declared ``FOR_FUN`` wants a hard-fought
friendly. Reading one as the other would double-count six strings across three
terms.
"""

from __future__ import annotations

from enum import Enum


class PlayIntent(str, Enum):
    """What kind of game a player wants, in one sport.

    Declared per ``(player, sport)`` — see ``play_intent_declaration.py`` for
    why that is its own aggregate rather than a field on the profile.
    """

    COMPETITIVE = "COMPETITIVE"
    FOR_FUN = "FOR_FUN"
    NO_PREFERENCE = "NO_PREFERENCE"


class PlayIntentSurface(str, Enum):
    """Which screen a declaration was made on.

    ``ConsentSurface``'s precedent in this same context, and it obeys the same
    rule about what it is *for*: it is context recorded beside a fact, never a
    thing any decision branches on.

    **It is client-asserted and a client could lie about it** (ADR-0094). That
    is accepted because the client is the only party that knows which screen it
    was, and nothing load-bearing reads it — which is exactly the condition
    under which a self-reported field is safe to keep.

    **It widened rather than renaming, and the reason was cost** (#280). The
    deck earned the fifth member: ``POST /deck`` has no mode to read, so it
    reads the declaration, is refused with ``play_intent_not_declared`` exactly
    as a search is, and draws the same interstitial. Reporting that as
    ``SEARCH_SWITCH`` was a small untruth in the one field whose whole job is to
    say which screen it was. The alternative argued was to rename
    ``SEARCH_SWITCH`` to ``PLAY_SWITCH`` — one value true of both Play surfaces
    rather than two that each name one — and it lost on cost, not on taste: the
    code is stored verbatim in ``PlayIntentDeclared`` and read back through
    ``PlayIntentSurface(event.surface)``, so a rename is an event migration
    bought on a field nothing branches on, while a widening is one member and
    leaves every code already in a stream meaning what it meant when it was
    written.
    """

    #: The end of a rating run that produced a rating. Every declaration starts
    #: life here: a rating is what makes a player matchable in a sport, so a run
    #: that was abandoned asks nothing.
    RATING_TAIL = "RATING_TAIL"
    #: The search screen's own toggle, taken as the edit surface. A settings
    #: screen is deliberately *not* one of these values. It names *that* screen
    #: alone; the other Play surface has ``DECK``.
    SEARCH_SWITCH = "SEARCH_SWITCH"
    #: The deck's sport chips, landing on a sport that is rated and undeclared
    #: — **as it was**. The deck reads no declaration since ``docs/adr/0169``
    #: §2 and draws no interstitial, so nothing emits this code any more; it
    #: stays in the closed five for the events that carry it, because a code
    #: already in a stream has to keep meaning what it meant when written.
    DECK = "DECK"
    #: The daily backstop, for the player who switched once, declined once and
    #: then searched in the new mode for a month.
    DRIFT_PROMPT = "DRIFT_PROMPT"
    PROFILE_SCREEN = "PROFILE_SCREEN"
