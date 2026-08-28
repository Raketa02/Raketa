"""The matchmaking context's refusals — twelve codes, distinct at four statuses.

**Distinct codes at the same status, because a client must be able to tell a
transient outage from a refusal about *you*.* Three of these are 503 and mean
very different things to somebody holding a phone: the engine raised, a
fail-closed read failed, the index is too far behind to be trusted. A single
``service_unavailable`` would collapse *try again in a moment* and *this feature
is off* into one line the client cannot branch on.

**An empty shortlist is a ``200``.** The honest empty state is an answer, not a
failure, and nothing here is raised for it — on the search that produced it and
on the read-back a month later alike.

**Never a fallback list.** When the engine is down the feature is down. A
hand-rolled backend ranker arriving as a hotfix is how a second, worse,
unexplainable ranking implementation enters the system permanently — so
:class:`MatchmakingUnavailable` is the whole of the recovery, and there is
deliberately nothing to catch it with.
"""

from __future__ import annotations

from http import HTTPStatus

from app.shared.domain.errors import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


class GateDataUnavailable(AppError):
    """A gate could not be evaluated, so the search refuses rather than guesses.

    **A gate that cannot be evaluated excludes** (``docs/adr/0095``). Blocks,
    holds and account state are safety controls, and *nobody is held* and *we
    could not find out* are different sentences: serving a shortlist on the
    second while printing the first is the one failure mode a matcher may not
    have.

    It is its **own code** rather than the generic transient one, because a
    client must be able to tell an outage that will pass from a refusal about
    *you* — ``account_held`` is a 403 about the searcher, and this is a 503 about
    the platform.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "gate_data_unavailable"


class MatchmakingUnavailable(AppError):
    """The engine raised. **The feature is down and there is no second ranker.**

    ``docs/adr/0093`` puts the scorer in-process, so it cannot be unreachable —
    only raise. What raises is an invariant: a malformed pairing, a ruleset the
    platform's vocabularies disagree with, a candidate row the index should never
    have held. None of those has a degraded answer, and a hand-rolled fallback
    list is the failure this refusal exists to make impossible.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "matchmaking_unavailable"


class IndexTooStale(AppError):
    """The index is far enough behind that a shortlist would be a guess.

    Past twenty-four hours the ladder refuses rather than serving
    (``index_staleness``), and **the refusal stands on quality, not safety** —
    every fact staleness can cost is a fact about who is *worth* meeting, because
    the facts that must be live never enter the index at all
    (``docs/adr/0111``). Between fifteen minutes and a day the search is served
    and the flag recorded.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "index_too_stale"


class SearchNotRecorded(AppError):
    """The telemetry could not be written, so the answer is not returned.

    ``docs/adr/0104``: the record is written in the request's own transaction and
    committed **before** the response — *the ``search_id`` is the answer's
    identity*. A shortlist returned without its row is a row of the product's own
    denominator lost forever, and there is no backfill.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "search_not_recorded"


class SportNotRated(ConflictError):
    """The searcher has no Skill rating for the sport they asked about.

    A conflict rather than a not-found, mirroring the shipped
    ``sport_already_rated`` one context over: the resource is the player's own
    rating and its state is what refuses. Settled by construction on the client —
    the sport chips are drawn only for rated sports — and this is the backstop
    for a stale profile on a second device.
    """

    code = "sport_not_rated"


class PlayerProfileNotCommitted(ConflictError):
    """The searcher has no profile, so there is no radius, grid or area to search
    with.

    **Not on the spec's error table**, and added here rather than folded into a
    neighbouring code. The client cannot reach the Play tab without a committed
    profile, so this is unreachable by design — which is exactly why it needs its
    own code: reusing ``sport_not_rated`` for it would tell a player to go and
    rate a sport they have already rated, and reusing a 500 would file a
    predictable refusal as a defect. It sits beside ``sport_not_rated`` at the
    same status because it is the same kind of fact: a refusal about *you*, which
    you can fix.
    """

    code = "player_profile_not_committed"


class PlayIntentNotDeclared(ConflictError):
    """The searcher has not said what kind of evening they are after.

    ``docs/adr/0094`` makes the search screen the edit surface for the
    declaration, so the client opens that interstitial **knowingly** and this is
    the backstop rather than the designed path.
    """

    code = "play_intent_not_declared"


class RungOfferNotFound(ConflictError):
    """This search cites a rung that was never offered to it.

    **An accepted widen is a new search citing the one that offered it**
    (``docs/adr/0099``), and the citation is checked rather than trusted: the
    radius a rung widens to is read off the offering search's own record, so a
    client that could name a rung nobody offered would have found the per-search
    radius input this contract does not have.

    It refuses instead of falling back to the strict search, because the two
    answers are different searches and the one the player asked for is the widened
    one. Silently running the narrow one would put a lie in the record: a row
    saying a rung was taken beside a pool that was never widened.
    """

    code = "rung_offer_not_found"


class SearchNotFound(NotFoundError):
    """No search of yours has that id.

    **A search that belongs to somebody else answers exactly as one that never
    existed**, and the sameness is the authorization rule rather than a
    convenience: an answer that separated them would tell a caller whether a
    stranger's ``search_id`` is real, which is a directory of other people's
    searches read one probe at a time.

    A search that returned nobody is **not** this. It is a `200` with an empty
    list, exactly as it was on the day it ran — the honest empty state is an
    answer, and a read-back that turned it into a 404 would forget a search that
    happened.
    """

    code = "search_not_found"


class AccountHeld(ForbiddenError):
    """The searcher is under a live hold. **The hold points both ways.**

    A held player can still sign in and run a search, which is why the gate is
    bidirectional and why the searcher's own side is refused here, at the entry
    point, rather than by hiding them from other people's lists
    (``docs/adr/0095``).
    """

    code = "account_held"


class OriginSearchNotFound(ConflictError):
    """A *Let's play* citing a search that never showed that person.

    **The origin key is refused, never linked as null** (``search-telemetry.md``
    §4). A silently dropped link is a denominator that lies: *interests per
    search* is how the whole engine is judged, and a row whose ``search_id`` is
    null is a yes that came from nowhere and is counted against nothing.

    Four ways this refuses, and they are one code on purpose — the search does
    not exist, it belongs to somebody else, it was run for another sport, or it
    never returned that person. Telling them apart would answer *does this
    ``search_id`` exist* for a stranger's id, which is the question the
    read-back's own 404 already declines to answer. It also swallows the
    degenerate case: your own search never returns *you*, so naming yourself
    lands here rather than needing a refusal of its own.

    It mirrors ``rung_offer_not_found`` deliberately, because it is the same
    shape of refusal — a client citing a row of this backend's that says
    something else — and the two should not answer differently.
    """

    code = "origin_search_not_found"


class OutstandingInterestCapReached(ConflictError):
    """This player already has the most yeses in flight that the sport allows.

    **The cap is hard, and it is shown before it bites** (``docs/adr/0127`` §3).
    ``OUTSTANDING_INTEREST_CAP`` is per sport, and past it the write is refused
    rather than silently making room: the *soft* cap — past it the oldest decays
    faster — reaches **backwards** and shortens the life of yeses already sent,
    under a rule the player was never told, because a twenty-first arrived.
    Nothing of theirs is quietly shortened to make room.

    The way out is waiting, or a mutual. There is deliberately no *release my
    oldest* gesture: that is the soft cap with the player's hand on it, and
    reinstating it needs an argument nobody has made.

    **The refusal code is contract and the number behind it is not**
    (``docs/adr/0106``). ``GET /api/v1/interest`` carries the outstanding count
    and the cap in force so a client can draw the limit rather than hardcode it —
    a cap the player cannot see is a refusal they cannot predict.
    """

    code = "outstanding_interest_cap_reached"
