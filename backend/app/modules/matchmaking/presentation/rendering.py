"""Turning the answer into the response, and omitting what does not apply.

**Every omitted field is omitted here, by not being passed.** The routes are
declared ``response_model_exclude_unset=True``, so a field this module does not
name is absent from the JSON — which is the whole mechanism behind
``docs/adr/0106`` §4's first spelling. A field this module passes as ``None`` is
the *second* spelling and means a measured nothing.

**Nothing here computes.** The Fit, its terms, the concerns, the modifiers and
the reason codes all arrive decided; the card and the at-stake block arrive
attached. What is left is naming fields — and a renderer that did arithmetic
would be a second implementation of a domain rule in the one layer nobody tests
for it.

**Every route renders the record**, and that is what makes the round trip true by
construction rather than by a test that happens to pass. A shortlist, a deal and
a search read back a month later reach :func:`_candidate` with the same
type — a ``SearchCandidateRecord`` — so there is no shape a fresh response could
carry that a stored one could not reproduce. The two departures the round trip
allows itself are the whole of the difference between these three functions: a
row the live gates now withhold, and the ``photo_url`` beside each recorded
``photo_id`` (``docs/adr/0109``, ``docs/adr/0107``). **The links are minted
before this module is called** — signing is I/O and nothing here does any — and
they arrive as a mapping the routes pass in, so a renderer cannot invent one for
a row that was not being shown.

**A withheld row carries no person.** It is a different type, not a candidate
with holes: there is no ``player_id`` on it and no card, so a client cannot
resurrect somebody the product has agreed to stop showing, and a renderer cannot
leak one by forgetting a branch.
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from app.kernel import InvariantViolated

from app.engines.matchfit.grouping import Arranged, Forecast, Split
from app.modules.matchmaking.application.forecast_lineup import ForecastAnswer
from app.modules.matchmaking.application.read_back_search import ReadBackAnswer
from app.modules.matchmaking.application.run_lineup_search import LineupAnswer
from app.modules.matchmaking.application.run_deck_deal import DeckAnswer
from app.modules.matchmaking.application.run_shortlist_search import ShortlistAnswer
from app.modules.matchmaking.domain.lineups import LineupSeat, Side as CourtSide
from app.modules.matchmaking.domain.prompts import RaisedPrompt
from app.modules.matchmaking.domain.relaxation import RungOffer
from app.modules.matchmaking.domain.searches import (
    InclusionReason,
    RecordedCard,
    SearchCandidateRecord,
    SearchRecord,
    SortOption,
)
from app.modules.matchmaking.presentation.schemas import (
    ArrangementSchema,
    ArrangementSeatSchema,
    CandidateSchema,
    ConcernSchema,
    ForecastResponse,
    ForecastSchema,
    LineupResponse,
    LineupSchema,
    LineupSeatSchema,
    OptimisedFor,
    PlayerCardSchema,
    PoolSchema,
    PromptSchema,
    RungOfferSchema,
    SearchEnvelope,
    ShortlistResponse,
    SidesSchema,
    SplitSchema,
    WireInclusionReason,
    WithheldRowSchema,
)
from app.modules.player_profile.domain.availability import AvailabilitySlot
from app.modules.player_profile.presentation.schemas import AvailabilitySlotResource


#: The links minted for this response, by player. **Not part of the record**:
#: a row absent from it has no photograph, and a photograph has no other
#: address — ``GET /photos/{id}`` signs only the asking player's own.
PhotoLinks = Mapping[UUID, str]


def render(answer: ShortlistAnswer, photos: PhotoLinks) -> ShortlistResponse:
    """The whole response, from the record the use case just wrote.

    Every row is live by construction — the gates were evaluated moments ago —
    so ``withheld`` is not passed at all, and the field does not appear.
    """

    return ShortlistResponse(
        search=_envelope(
            answer.record, answer.sorts_available, prompts=answer.prompts
        ),
        candidates=[_candidate(row, photos) for row in answer.record.returned],
    )


def render_deal(answer: DeckAnswer, photos: PhotoLinks) -> ShortlistResponse:
    """One deal, in **the same shape a shortlist crosses in**.

    Not a shape of its own, and that is the read-back's requirement rather than
    tidiness: ``GET /searches/{id}`` returns the same schema the `POST` did, for
    any of the four surfaces, so a deal that crossed in a second shape would be a
    deal that could not be read back through the one renderer this module has.

    What differs is what the record says. ``mode`` is ``null`` — exactly on the
    deck and nowhere else — the sort list is empty, and ``rung_offers`` is
    ``null`` because the ladder does not reach here and the offers were not
    computed at all.

    ``prompts`` is passed, and an empty list is the honest answer on a deal that
    ran on the profile's own week: the deck accepts an improvised grid now, so it
    owes the offer to keep one. Only that prompt can appear here — the ladder
    still does not reach the deck, and the two loops' prompts are read beside a
    shortlist.
    """

    return ShortlistResponse(
        search=_envelope(
            answer.record, answer.sorts_available, prompts=answer.prompts
        ),
        candidates=[_candidate(row, photos) for row in answer.record.returned],
    )


def render_read_back(
    answer: ReadBackAnswer, photos: PhotoLinks
) -> ShortlistResponse:
    """The same response, a month later, minus who we may no longer show.

    **The list keeps its length and its order.** A withheld row holds its place
    and says what happened to it; a row that still stands says so positively,
    because *we re-checked and this one is fine* is the other half of the
    statement and a client should not have to infer it from an absence.
    """

    return ShortlistResponse(
        search=_envelope(answer.record, answer.sorts_available),
        candidates=[
            WithheldRowSchema(withheld=True)
            if row.withheld
            else _candidate(row.recorded, photos, withheld=False)
            for row in answer.rows
        ],
    )


def render_lineup(answer: LineupAnswer, photos: PhotoLinks) -> LineupResponse:
    """The seated four: the envelope, the rows, and the court they sit on.

    **The rows come off the record**, exactly as a shortlist's do, so a seated
    card carries the same number the shortlist showed and nothing is re-scored
    behind the player's back. The court is beside them because a seat is a fact
    about *this* answer rather than about a person.

    ``optimised_for`` is ``GROUP`` when the searcher hand-seated anybody: from
    that moment the engine is filling seats around them and may hand the searcher
    a worse individual match than an empty court would have, and the screen has
    to be able to say so rather than leave it to be discovered.
    """

    return LineupResponse(
        search=_envelope(
            answer.record,
            answer.sorts_available,
            prompts=answer.prompts,
            optimised_for=(
                OptimisedFor.GROUP
                if answer.optimised_for_group
                else OptimisedFor.SEARCHER
            ),
        ),
        # **The same rows, in the same shape, on every surface.** A line-up's
        # returned band is who sat down, so the list is the seated four minus
        # the searcher — and a client that renders a shortlist row can render
        # this one without a branch.
        candidates=[_candidate(row, photos) for row in answer.record.returned],
        lineup=LineupSchema(
            seats=[_seat(seat) for seat in answer.seats],
            arrangements=_arrangements(
                answer.arrangements,
                current=answer.evenest,
                best=answer.best,
                evenest=answer.evenest,
            ),
            **_group_reason(answer),
        ),
    )


def render_forecast(answer: ForecastAnswer) -> ForecastResponse:
    """Three arrangements of a composed four. **No search, so no envelope.**

    Nothing was generated, ranked or recorded, so there is no ``search_id`` to
    read this back by and no row to render. What crosses is the arithmetic and
    the two stamps that make it reproducible.
    """

    return ForecastResponse(
        arrangements=_arrangements(
            answer.arrangements,
            current=answer.current,
            # **No objective was computed here and none is claimed.** Nothing was
            # compared to anything: the caller composed this four themselves, and
            # a forecast has no Fits to read a seat by. So ``is_best`` is omitted
            # on every arrangement rather than pointed at the seat order the
            # client happened to send.
            best=None,
            evenest=answer.evenest,
        ),
        engine_version=answer.engine_version,
        ruleset_version=answer.ruleset_version,
    )


def _group_reason(answer: LineupAnswer) -> dict[str, Any]:
    """The two codes a line-up may or may not have to say.

    Both are **omitted rather than sent as null**, and they mean different
    things: no ``group_reason`` is *there was no runner-up to beat*, and no
    ``dock`` is *the four of you do share an hour*. A null in either place would
    read as a measured nothing, which neither is.
    """

    fields: dict[str, Any] = {}
    if answer.group_reason is not None:
        fields["group_reason"] = answer.group_reason
    if answer.dock is not None:
        fields["dock"] = answer.dock
    return fields


def _arrangements(
    ways: tuple[tuple[Arranged, tuple[LineupSeat, ...]], ...],
    *,
    current: Arranged | None,
    best: Arranged | None,
    evenest: Arranged | None,
) -> list[ArrangementSchema]:
    """Every way round, each marked by **identity and never by re-deriving.**

    ``is_best`` and ``is_evenest`` are two separate booleans because the new fact
    the builder can state is that they **differ**, and they are compared by
    object identity against what the engine chose — a renderer that recomputed
    either would be the second implementation of a domain rule that
    ``docs/adr/0108`` exists to prevent.

    ``best`` is ``None`` wherever no objective was computed — an incomplete
    four, a singles line-up, every forecast — and then **``is_best`` is omitted
    from every arrangement** rather than set false on all three or pointed at
    whichever one is being drawn. Omitted is *this does not apply here*, which is
    exactly the case; ``false`` everywhere would say the engine looked and found
    no best.
    """

    return [
        ArrangementSchema.model_validate(
            {
                "pairing_id": position,
                "is_current": one is current,
                "is_evenest": one is evenest,
                "sides": SidesSchema(
                    A=[
                        _arranged_seat(seat)
                        for seat in seats
                        if seat.side is CourtSide.A
                    ],
                    B=[
                        _arranged_seat(seat)
                        for seat in seats
                        if seat.side is CourtSide.B
                    ],
                ),
                "forecast": _forecast(one.forecast),
                "split": _split(one.split),
                **({} if best is None else {"is_best": one is best}),
            }
        )
        for position, (one, seats) in enumerate(ways, start=1)
    ]


def _split(split: Split) -> SplitSchema:
    """The two strengths and the gap between them, **passed through.**

    ``gap`` is read off the engine's own value rather than subtracted here: the
    whole point of serving it is that there is one subtraction in the system, and
    a renderer doing its own would be the second one.
    """

    return SplitSchema(
        your_side=split.your_side,
        their_side=split.their_side,
        gap=split.gap,
    )


def _arranged_seat(seat: LineupSeat) -> ArrangementSeatSchema:
    """One seat inside one arrangement. **The person by id, never twice over.**

    The candidate rides once, in the top-level ``seats`` list; an arrangement
    names who sits where and lets the client look them up, because three copies
    of four breakdowns is three chances for two of them to disagree.
    """

    fields: dict[str, Any] = {
        "seat_index": seat.seat_index,
        "relationship": seat.relationship,
    }
    if seat.player_id is not None:
        fields["player_id"] = seat.player_id
    return ArrangementSeatSchema.model_validate(fields)


def _seat(seat: LineupSeat) -> LineupSeatSchema:
    """One seat on the current court, naming whoever is in it.

    **The id and never the breakdown.** The four people ride once, in
    ``candidates``, which is the list every surface returns and the one a
    read-back reproduces; repeating them here and again in three arrangements
    would be four copies of one card with four chances to disagree.

    The searcher's own seat names nobody: they are not a row of their own search,
    and a card for yourself is a shape this contract has never had.
    """

    fields: dict[str, Any] = {
        "side": seat.side,
        "seat_index": seat.seat_index,
        "relationship": seat.relationship,
    }
    if seat.player_id is not None:
        fields["player_id"] = seat.player_id
    if seat.unfilled_reason is not None:
        fields["unfilled_reason"] = seat.unfilled_reason
    return LineupSeatSchema.model_validate(fields)


def _forecast(forecast: Forecast) -> ForecastSchema:
    """How even the game is, with its caveat **inside** it.

    ``provisional`` is derived from the assumption on the engine's own type and
    is passed through rather than recomputed, because the failure being guarded
    against is a screen showing the number without its caveat — and a renderer
    that decided the boolean for itself is exactly where the two come apart.
    """

    return ForecastSchema(
        pct=forecast.pct,
        sigma_group=forecast.sigma_group,
        provisional=forecast.provisional,
        assumption=(
            None if forecast.assumption is None else forecast.assumption.value
        ),
    )


def _envelope(
    record: SearchRecord,
    sorts: tuple[SortOption, ...],
    *,
    prompts: tuple[RaisedPrompt, ...] | None = None,
    optimised_for: OptimisedFor = OptimisedFor.SEARCHER,
) -> SearchEnvelope:
    """The search's own facts, and the two that are about *now*.

    ``prompts`` is ``None`` for *do not mention it at all* — the read-back, where
    a month-old question would be asked about a value that has since moved — and
    a list on the `POST`, where an empty one honestly says the search raised
    none.
    """

    pool = record.pool_description
    fields: dict[str, Any] = {}
    if prompts is not None:
        fields["prompts"] = [_prompt(raised) for raised in prompts]
    # **Omitted rather than sent as null**, which is this module's own first
    # spelling: a search recorded before the area was kept did not measure a
    # nothing, it recorded nothing at all — and a card handed an empty code would
    # compare it unequal to every real one and quietly say *never in your area*.
    if record.searcher_area_code is not None:
        fields["my_area_code"] = record.searcher_area_code
    return SearchEnvelope(
        search_id=record.id,
        at=record.at,
        surface=record.surface,
        mode=record.mode,
        ruleset_version=record.ruleset_version,
        engine_version=record.engine_version,
        # A shortlist optimises for the person who asked, always, and so does an
        # empty court. The field is on the envelope rather than implied by the
        # surface because a line-up **with seats locked** is the case where it is
        # not, and one renderer should read one fact.
        optimised_for=optimised_for,
        index_stale=record.index_stale,
        pool=PoolSchema(
            sport=pool.sport,
            radius_km_used=pool.radius_km_used,
            players_in_range=pool.players_in_range,
            window=pool.window,
            post_gate=pool.post_gate,
        ),
        radius_clamp=record.radius_clamp_bit,
        sorts_available=list(sorts),
        # **`None` and an empty list are different answers.** `None` is *the
        # offers were not computed at all*; `[]` is *computed, and there is
        # nothing left to offer* — which is the honest empty state, where the
        # pool description beside it is the whole of what can be said.
        rung_offers=(
            None
            if record.rung_offers is None
            else [_offer(offer) for offer in record.rung_offers]
        ),
        **fields,
    )


def _offer(offer: RungOffer) -> RungOfferSchema:
    """One rung as it crosses. The payload field its ask does not use is omitted,
    not sent as null: a radius rung has no slot, rather than a slot of nothing.

    **The cell is read out of its code**, by ``_cell`` below. A times rung's slot
    is drawn on the client's own grid beside twenty other cells, and no client
    ever splits ``"4:EVENING"`` for itself
    (`#283 <https://github.com/Raketa02/Raketa/issues/283>`_).
    """

    fields: dict[str, Any] = {
        "rung": offer.rung,
        "ask": offer.ask,
        "candidates_above_floor": offer.candidates_above_floor,
        "window": offer.window,
    }
    if offer.radius_km is not None:
        fields["radius_km"] = offer.radius_km
    if offer.slot is not None:
        fields["slot"] = _cell(offer.slot)
    return RungOfferSchema.model_validate(fields)


def _cell(code: str) -> AvailabilitySlotResource:
    """One stored code, as the two named fields a grid is drawn from.

    **The only place this side reads our own slot encoding**, and it is one
    function rather than two identical expressions because the rule it enforces
    is that there is no second answer — a cell that gets drawn crosses in these
    two fields, whether the player ticked it (``availability``), was offered it
    (``RungOfferSchema.slot``, #283) or is being asked to keep it
    (``PromptSchema.slots``, #286). ``AvailabilitySlotResource``'s own docstring
    carries the argument; this carries the arithmetic.
    """

    cell = AvailabilitySlot.from_code(code)
    return AvailabilitySlotResource(day=int(cell.day), part=cell.part)


def _prompt(raised: RaisedPrompt) -> PromptSchema:
    """One standing question, carrying only the value it is asking about.

    **The week goes through the same ``_cell`` the offered slot does.** That this
    one is a payload *quoted back* rather than a resource the player asked for
    changes nothing about who owns the encoding: the sheet draws it on the
    seven-by-three grid beside the profile's own week, and a cell that gets drawn
    crosses in two named fields
    (`#286 <https://github.com/Raketa02/Raketa/issues/286>`_).
    """

    fields: dict[str, Any] = {"prompt": raised.prompt}
    if raised.radius_km is not None:
        fields["radius_km"] = raised.radius_km
    # ``is not None`` and never truthiness: **an empty list is a cleared week**
    # and has to cross, where omitting it would ask *keep these times?* about no
    # times at all and leave the sheet with nothing to draw.
    if raised.slots is not None:
        fields["slots"] = [_cell(code) for code in raised.slots]
    if raised.mode is not None:
        fields["mode"] = raised.mode
    return PromptSchema.model_validate(fields)


def _candidate(
    row: SearchCandidateRecord,
    photos: PhotoLinks,
    *,
    withheld: bool | None = None,
) -> CandidateSchema:
    """One recorded row on the wire.

    ``withheld`` is ``None`` for *do not mention it at all* — the `POST`, where
    every row is live by construction — and ``False`` on a read-back, where the
    gates were re-evaluated and this row still stands. It is never ``True`` here:
    a withheld row is a different type and never reaches this function.
    """

    card = row.card
    if card is None:  # pragma: no cover — the record's own invariant refuses one
        # A ``RETURNED`` row holds a card by construction: the biconditional on
        # ``SearchCandidateRecord`` says so, and a row whose card could not be
        # assembled was dropped before it was ever written. Refused in the
        # kernel's own shape rather than rendered with a hole where a person is.
        raise InvariantViolated("a returned row with no card reached the wire")
    fields: dict[str, Any] = {
        "player_id": row.player_id,
        "fit": row.fit,
        "player_card": _card(card, photos.get(row.player_id)),
        "concerns": [ConcernSchema(term=term) for term in row.concerns],
        # The same mappings the record stores. One serialiser, two consumers:
        # the wire validates it into the discriminated union and the store keeps
        # it opaque, so the published shape and the stored blob cannot drift into
        # disagreeing about a field name.
        "terms": [dict(term) for term in row.terms],
        # **Index-aligned.** The record keeps the basis and whose gap each
        # entry is in two columns, for the queryability the first one's own
        # migration argues for. A row where the two had drifted is refused by
        # ``SearchCandidateRecord`` itself, on the way in and again on the way
        # back out, so this zip is strict as a statement of that rule rather
        # than as the place it is caught.
        "degraded_terms": [
            {"term": term, "reason": reason}
            for term, reason in zip(
                row.degraded_terms, row.degraded_reasons, strict=True
            )
        ],
        "modifiers": [dict(modifier) for modifier in row.modifiers],
        "liveness_reasons": list(row.liveness_reasons),
    }
    if row.distance_km is not None:
        # Omitted rather than sent as zero when the term stood down, which is
        # what lets *Closest* sort a stood-down row last instead of first.
        fields["distance_km"] = row.distance_km
    if row.inclusion_reason is InclusionReason.INTEREST_LIFT:
        # **Only a reason that admits somebody crosses**, and the test is the
        # value rather than its presence: the store holds three and two of them
        # merely reorder. `NEWCOMER_WINDOW` reaches the client as a Liveness
        # reason instead, and `ZERO_EXPOSURE` never crosses at all — *nobody has
        # been shown them all week* is a third party's unpopularity.
        fields["inclusion_reason"] = WireInclusionReason.INTEREST_LIFT
    if row.at_stake is not None:
        fields["at_stake"] = {
            "win_delta": row.at_stake.win_delta,
            "loss_delta": row.at_stake.loss_delta,
        }
    if withheld is not None:
        fields["withheld"] = withheld
    return CandidateSchema.model_validate(fields)


def _card(card: RecordedCard, photo_url: str | None) -> PlayerCardSchema:
    """The card as it was shown, from the row that recorded it — **and the one
    field that was not shown to it.**

    The link arrives as an argument rather than being looked up here, because it
    is not on the card: the record holds an id and a URL signed over it is a fact
    about *this response*. ``None`` is *this row has no photograph*, and then
    **both fields are omitted together** — an id with no link beside it is a
    photograph nothing can draw, which is the contract this field exists to
    close.

    A row that recorded an id and was minted no link is drawn the same way, and
    that is deliberate rather than an oversight: the generated court poster is
    already what this card falls back to, and a search that failed over a
    signature would be the whole feature going down for the least of its facts.

    ``counted_games`` is never passed: the games ledger has no provider in this
    build, so the field does not apply and a zero would be an invented one.

    It takes a card and never an absence, so *a row with no person on it* is not
    a state this function has to have an opinion about.
    """

    fields: dict[str, Any] = {
        "nickname": card.nickname,
        "area_code": card.area_code,
        "social_tags": list(card.social_tags),
        "level": card.level,
        "band": card.band,
        # Nested on the wire, flat on the record. Copied either way — see
        # `CandidateRow.range_low`.
        "range": {"low": card.range_low, "high": card.range_high},
    }
    if card.photo_id is not None and photo_url is not None:
        fields["photo_id"] = card.photo_id
        fields["photo_url"] = photo_url
    return PlayerCardSchema.model_validate(fields)
