"""Reading one player's record. **Two use cases, one assembler.**

``ReadPlayerRecord`` answers about somebody else and runs the admission rule
first; ``ReadOwnRecord`` answers about the person asking and has no admission
collaborator to run. ``docs/adr/0159`` calls that *the same assembler with the
gate short-circuited*, and the short circuit is spelled in the **wiring** rather
than as a branch:

- the ``/me`` route declares no gate machinery, so a process whose candidate
  index is not running still serves a player their own record. The gates bind the
  index once per evaluation (``docs/adr/0112``) and refuse the whole read when
  there is none — correct for a sheet about a stranger, and absurd for the one
  screen that tells a player how they appear.
- there is no branch anybody can delete. A use case that took an admission and
  skipped it when ``reader == subject`` is one refactor away from skipping it
  when it should not.

**The assembler does no arithmetic and holds one rule.** It reads identity, mints
one link, says whether the record is the reader's own, and resolves **which sport
the sheet is about** — the single thing here nobody else could decide, because it
is a question about the reader rather than about the subject. Every figure that
lands on this sheet arrives from the context that owns it, already decided.

**One zone is answered differently depending on who is reading, and it is the
only one.** What other players said crosses as a figure and a count for a
stranger, and as a coarse band with neither for the subject — because an average
beside a count in front of the person it is about is a subtraction that names
each new rating exactly, and they know who they played (``docs/adr/0158``). The
branch is on ``is_self``, which the assembler already holds; what makes it safe
is that the *port* has two methods and the subject's one cannot say the figure,
so a branch taken the wrong way asks for something that does not exist rather
than quietly publishing something that does. ``PlayerRecord`` refuses the pair
outright if one ever arrives beside ``is_self``.

**The sport asked for reaches the sheet's contents and never its admission.** It
selects which Level is printed; the four fail-closed gates run in the partition of
the **disclosure**, which is a fact the platform holds. A record refused in a
sport a client sent would be a client choosing whether it may see somebody
(``docs/adr/0159``).

**One clock, read once, handed down.** The run of form, the metered rows and the
variety fold are all folded against an instant, and the record's own gate against
the same one — two reads of the clock in one response is how a sheet ends up
admitting a pair on one instant and describing them on another. It matters most
on the rows: a plan is a ghost only once its entry window has closed and a seat
has lapsed only once its day has run out, so two presents would publish a pill
whose strands disagree with the variety beside them about which games exist.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport
from app.modules.player_record.application.admission import RecordAdmission
from app.modules.player_record.domain.errors import (
    RECORD_UNAVAILABLE,
    RecordUnavailable,
)
from app.modules.player_record.domain.ports import (
    RecordPhotoLink,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
)
from app.modules.player_record.domain.record import (
    GameOutcome,
    PlayerRecord,
    SkillPanel,
    SubjectRating,
)
from app.modules.player_record.domain.sport_choice import pills_of, sport_to_print


async def assemble_record(
    *,
    subject_id: UUID,
    is_self: bool,
    arrived_from: Sport | None,
    now: Instant,
    identities: SubjectIdentitySource,
    photos: RecordPhotoLink,
    ratings: SubjectRatings,
    form: SubjectForm,
    reliability: SubjectReliability,
    variety: SubjectVariety,
    sportsmanship: SubjectSportsmanship,
) -> PlayerRecord:
    """The record itself, once somebody has decided it may be read.

    **It refuses when the platform cannot describe the person**, and it refuses
    in the one shape this context refuses in — an id nobody has been issued, a
    handle that cannot be read and a profile that was never committed are one
    answer here, because they have one remedy and separating them would answer
    *is this id real* about a stranger.

    **A player rated in nothing costs no run of form.** The sheet is about no
    sport, so there is no sport to ask a run about, and the question is not asked
    rather than being asked and thrown away — which is the difference between a
    newcomer's record being cheap and it being the same price as anybody's.

    **The rows, the variety and what players said are asked for regardless,
    because none of them is about a sport.** The four absences are four different
    questions and the sheet must not conflate them: a person rated in nothing may
    have played all week, a person rated in four sports may never have had a game
    counted, a person with a full record of games may have had nothing at all
    *fall due*, and a person with a perfect record of turning up may have been
    rated by nobody — nobody is obliged to answer a card, and not answering leaves
    no record of the omission.

    **Exactly one of the two sportsmanship questions is asked**, and which one is
    the only thing on this sheet that ``is_self`` decides beyond a title. A reader
    is answered with the figure and its count; the subject is answered with a
    coarse band and neither. The other is not asked and thrown away — it is not
    asked, so the figure never enters this process on a sheet about the person it
    is about.
    """

    identity = await identities.identity_of(subject_id)
    if identity is None:
        raise RecordUnavailable(RECORD_UNAVAILABLE)
    photo_url = (
        None
        if identity.photo_id is None
        else await photos.link_for(
            # **Signed as the person on the record**, never as the person
            # looking: an object store keys the pair, so a link signed under the
            # reader's id would reach an object that does not exist.
            owner_id=subject_id,
            photo_id=identity.photo_id,
        )
    )
    held = await ratings.ratings_of(subject_id)
    printed = sport_to_print(arrived_from, held)
    skill = (
        None
        if printed is None
        else _panel(
            held[printed],
            last_five=await form.last_results_in(subject_id, sport=printed, now=now),
        )
    )
    return PlayerRecord(
        is_self=is_self,
        identity=identity,
        photo_url=photo_url,
        sports=pills_of(held),
        skill=skill,
        reliability=await reliability.reliability_of(subject_id, now=now),
        variety=await variety.variety_of(subject_id, now=now),
        sportsmanship=(
            None if is_self else await sportsmanship.what_players_said(subject_id)
        ),
        sportsmanship_band=(
            await sportsmanship.band_for(subject_id) if is_self else None
        ),
    )


def _panel(rating: SubjectRating, *, last_five: tuple[GameOutcome, ...]) -> SkillPanel:
    """The rating plus the run, and nothing derived from either.

    Written out rather than spread, so a field added to ``SubjectRating`` that
    does **not** belong on the printed panel is a decision somebody makes here
    rather than one that happens.
    """

    return SkillPanel(
        sport=rating.sport,
        level=rating.level,
        band=rating.band,
        confidence=rating.confidence,
        counted_games=rating.counted_games,
        likely_range=rating.likely_range,
        last_five=last_five,
    )


@final
class ReadPlayerRecord:
    """Somebody else's record, read through what entitled the reader to it."""

    def __init__(
        self,
        *,
        admission: RecordAdmission,
        identities: SubjectIdentitySource,
        photos: RecordPhotoLink,
        ratings: SubjectRatings,
        form: SubjectForm,
        reliability: SubjectReliability,
        variety: SubjectVariety,
        sportsmanship: SubjectSportsmanship,
        clock: Clock,
    ) -> None:
        self._admission = admission
        self._identities = identities
        self._photos = photos
        self._ratings = ratings
        self._form = form
        self._reliability = reliability
        self._variety = variety
        self._sportsmanship = sportsmanship
        self._clock = clock

    async def execute(
        self, *, reader_id: UUID, subject_id: UUID, arrived_from: Sport | None = None
    ) -> PlayerRecord:
        """**Gate first, and everything else afterwards.**

        The order is the decision: a read that fetched a stranger's handle,
        photograph and area and *then* refused would have performed the lookup
        the admission rule exists to prevent, and would have paid for it besides.

        ``is_self`` is read off the same comparison the admission's first strand
        makes, and that is one comparison used for two purposes rather than a
        rule spelled twice: one decides whether a gate is owed, the other decides
        what the sheet is titled.

        ``arrived_from`` reaches the assembler and **never the admission**. It
        says which sport the sheet is about; who may be seen is decided in the
        partitions of the disclosure, which the platform holds and a client does
        not send. A caller passing a sport they were never shown this person in
        changes what is printed and nothing about whether it is.
        """

        now = self._clock.now()
        if not await self._admission.admits(
            reader_id=reader_id, subject_id=subject_id, now=now
        ):
            raise RecordUnavailable(RECORD_UNAVAILABLE)
        return await assemble_record(
            subject_id=subject_id,
            is_self=reader_id == subject_id,
            arrived_from=arrived_from,
            now=now,
            identities=self._identities,
            photos=self._photos,
            ratings=self._ratings,
            form=self._form,
            reliability=self._reliability,
            variety=self._variety,
            sportsmanship=self._sportsmanship,
        )


@final
class ReadOwnRecord:
    """Your own record — *How others see you*, and nothing gates it.

    A block is between two people, the gender preference is mutual, and neither
    has anything to say about somebody reading their own sheet. A hold does not
    reach it either: a held player is refused every surface that would show them
    to somebody else, and this is the one that shows them to themselves.
    """

    def __init__(
        self,
        *,
        identities: SubjectIdentitySource,
        photos: RecordPhotoLink,
        ratings: SubjectRatings,
        form: SubjectForm,
        reliability: SubjectReliability,
        variety: SubjectVariety,
        sportsmanship: SubjectSportsmanship,
        clock: Clock,
    ) -> None:
        self._identities = identities
        self._photos = photos
        self._ratings = ratings
        self._form = form
        self._reliability = reliability
        self._variety = variety
        self._sportsmanship = sportsmanship
        self._clock = clock

    async def execute(
        self, *, reader_id: UUID, arrived_from: Sport | None = None
    ) -> PlayerRecord:
        """**Still no gate, and now a clock.** The instant is read for the run of
        form and for nothing else here — a sheet about yourself has nothing to
        re-evaluate."""

        return await assemble_record(
            subject_id=reader_id,
            is_self=True,
            arrived_from=arrived_from,
            now=self._clock.now(),
            ratings=self._ratings,
            form=self._form,
            reliability=self._reliability,
            variety=self._variety,
            sportsmanship=self._sportsmanship,
            identities=self._identities,
            photos=self._photos,
        )


__all__ = [
    "ReadOwnRecord",
    "ReadPlayerRecord",
    "assemble_record",
]
