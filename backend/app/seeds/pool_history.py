"""**Everybody in her pool has played**, so every face she taps has a record.

The cohort's own played history exists to reach *card states* — a full run, a gap, a
count with no run, an absence — and reaches them with seven members. Her record sheet
needed a second list. This is the third, and it answers a different question again:
**can a developer tap any face and get a filled sheet**, without playing a game or
answering a card by hand.

**It is a development convenience and says so.** In production most players will be
missing most of this, and that is the natural state rather than a defect — a record is
what the platform *watched*, and it watches nothing about somebody who has not played.
What this buys is that a screen can be developed against a filled sheet without waiting
for a population to accumulate one, which is the argument ``cohort.py`` already makes
about its own rings.

## One search, because only one is guaranteed to find everybody

Four of the five courts here are **organised by the protagonist**, and that is
mechanical rather than stylistic. A court cites the search that showed the people it
seats, and a padel court seats three of them — so one search has to return three named
accounts before the shortlist fills at twenty. Hers is the only search on this platform
that provably returns her whole pool.

The fifth is ``cohort-a-16``'s, and it is the one alternative that works: a member
searching at the slider's floor sees their own ring at nought kilometres and nobody from
the centre, so the list cannot fill before it finds everybody named. It is the mechanism
the cohort's own padel doubles already runs on.

**What that costs is that she is on four of the five courts**, so she states every score
on them and the two people opposite are the ones a score is put to.

## Two faces are not here, and each has a measured reason

**``the-newcomer``** committed three days ago, and a three-day-old account with a full
record is a lie about how a record accumulates. It is also the pool's **absent**
witness: ``_refuse_a_card_the_platform_watched_nothing_of`` needs one and this layer
leaves no other, which makes the omission load-bearing rather than merely honest.

**``the-blank-week-player``** cleared their week, so ``AVAILABILITY_OVERLAP`` stands
down on every row of theirs and her search never returns them at any instant this list
uses. That was measured rather than assumed. Their own ring is the centre, which no
same-ring organiser reaches, so there is no court to put them on either.

## What it does not do

**It changes no draw.** Nothing here reaches ``SECOND_SPORT_BECAUSE_THEY_PLAYED`` or
``_how_far_they_have_to_see``: every row is padel, everybody on one already holds padel,
and the only new organiser is not a cohort member at all. ``cohort.json`` is
byte-identical with this list added.

**It writes nothing by hand.** Every game is a real challenge really accepted with a
real score really entered, through the same use cases a request runs.
"""

from __future__ import annotations

from typing import Final, Mapping

from app.kernel import Sport
from app.seeds.catalog import ACCOUNTS, PROTAGONISTS, THE_NEWCOMER, SeedAccount
from app.seeds.cohort import (
    COHORT,
    GHOSTED_AT_LEAST_DAYS_AGO,
    PLAYED_AT_LEAST_DAYS_AGO,
    PLAYED_GAMES,
    PROTAGONIST_GAMES,
    PROTAGONIST_HANDLE,
    RATED_WITHIN_DAYS,
    STARS_ARE_ONE_TO_FIVE,
    Cohort,
    PlayedGame,
)
from app.seeds.relationships import RELATIONSHIP_ACCOUNTS

#: Every account that is not a cohort member, by the handle a declaration names it
#: with. **Their slug is their handle** — the catalog's own rule: an account is named
#: for the state it represents, and the address is derived from that name.
NAMED_ACCOUNTS: Final[Mapping[str, SeedAccount]] = {
    account.slug: account
    for account in (*ACCOUNTS, *PROTAGONISTS, *RELATIONSHIP_ACCOUNTS)
}


def address_of(handle: str, cohort: Cohort = COHORT) -> str:
    """The address behind a handle, from **any** of the three populations.

    One resolver rather than three, because a declaration names people by handle and
    does not know or care which list they came out of: the cohort is a distribution,
    the catalog is a set of named states, the eleven are pair fixtures — and a court
    seats whoever it seats.
    """

    if handle.startswith("cohort-"):
        return cohort.by_handle(handle).email
    account = NAMED_ACCOUNTS.get(handle)
    if account is None:
        raise RuntimeError(
            f"'{handle}' is named on a court and is in none of the three "
            f"populations: it is not a cohort handle, and no named account "
            f"carries that slug."
        )
    return account.email


def handle_of(address: str, cohort: Cohort = COHORT) -> str:
    """:func:`address_of` read the other way, for the report and the assertions."""

    for member in cohort.members:
        if member.email == address:
            return member.handle
    for slug, account in NAMED_ACCOUNTS.items():
        if account.email == address:
            return slug
    return address


#: How far back the pool's record goes. **Past the sportsmanship card's own week, and
#: that is the decision rather than a slack bound** (#384).
#:
#: The week below was the whole of this layer, on the argument that *a court older than
#: that can be played and never rated, and a face with a record and no stars is half of
#: what this is for*. Two things made half of it the wrong half. **A record needs depth
#: and depth needs days**: *Last 5* draws one square per counted result and nobody may
#: play twice on a day, so seven usable days is a ceiling of seven results — and the
#: protagonist, whose search is the only one that provably reaches her whole pool, was
#: **booked on every one of them** by her own tennis history. Not one more court could
#: be
#: organised at all. And the two wants pull in opposite directions rather than together:
#: the card wants a court inside its week, the record wants courts spread over a career.
#:
#: So the layer splits. :data:`THE_RATEABLE_WEEK` stays exactly as it was — five courts,
#: unchanged, and the only ones :data:`WHAT_THE_POOL_SAID` may name — and
#: :data:`THE_RECORD_GOES_BACK` holds the older ones, which buy the record half and say
#: so. A face with stars is still a face with stars; a face with a record and no stars
#: is
#: now most of them, which is what a record looks like in production anyway.
#:
#: **Thirty days, and the bound is a real one.** A game may not predate the profile of
#: somebody who played it, the relationship accounts commit at forty, and the refusal
#: below reads both — so this is the widest window every named account can be seated in
#: without the ceiling becoming somebody's commit date. Four cohort members commit
#: inside
#: it and are refused out of the older courts by that same rule rather than by a list.
THE_RECORD_GOES_BACK_DAYS: Final = 30

#: **The courts inside the sportsmanship card's own week, and the only ones anybody may
#: be asked about.** Read down the endings rather than the scores.
#:
#: - Five courts, three other people on each. Two seat somebody for a *second* evening,
#:   which is the whole of why *opponent variety* reads as anything but a flat 100%
#:   anywhere in this pool.
#: - The four-day-old row is the one **nobody answered**: she states the score, the two
#:   opposite ignore it, silence confirms it anyway, and both carry an ignored result.
#:   Without it every strand here would publish 100%, and the ladder that tints the pill
#:   would have one colour in the whole pool.
#: - The days are the ones **her tennis history leaves free**, and all of them sit
#:   inside the sportsmanship card's own week: this is the half of the layer that buys
#:   stars, and a court outside the week buys none.
#: - Everybody is settled clear of the newcomer window except ``cohort-a-06``, who
#:   committed six days ago and so appears on the five-day-old court and nowhere older.
THE_RATEABLE_WEEK: Final[tuple[PlayedGame, ...]] = (
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=8,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-05"),
        side_b=("cohort-a-07", "the-one-sport-player"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=7,
        side_a=(PROTAGONIST_HANDLE, "said-yes-to-you"),
        side_b=("they-turned-down-your-court", "your-yes-makes-it-mutual"),
        won_by="B",
    ),
    # **The court `cohort-a-16` sends, and the only one she is not on.** `cohort-a-06`
    # committed six days ago and her search never returns them; `cohort-a-16` searches
    # at the slider's floor, so their pool is their own ring at nought kilometres and
    # nobody from the centre is in the way.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=5,
        side_a=("cohort-a-16", "cohort-a-06"),
        side_b=("cohort-a-10", "cohort-a-11"),
        won_by="B",
    ),
    # **The one nobody answered.** The score stands — silence confirms it — so the
    # square is drawn and the dock lands on the two it was put to.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=4,
        side_a=(PROTAGONIST_HANDLE, "you-passed-them"),
        side_b=("you-said-yes-to-them", "cohort-a-13"),
        won_by="A",
        answered=False,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=2,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-07"),
        side_b=("cohort-a-05", "cohort-a-11"),
        won_by="B",
    ),
)

#: **The courts that give the record its depth, and buy no stars.** Everything here is
#: older than :data:`RATED_WITHIN_DAYS`, which is what makes it possible at all: the
#: protagonist has a game on every single day the week has room for, and one court a day
#: is the ceiling *Last 5* imposes by being ordered on the instant a game was played.
#:
#: **She organises all but three, and that is mechanical.** A court cites the search its
#: seats came off, and hers is the only search that provably returns the whole pool —
#: which is the same argument :data:`THE_RATEABLE_WEEK` already runs on. The exceptions
#: are ``cohort-a-16``'s, and they exist because three members committed *inside* this
#: window and cannot be seated in it at all: ``cohort-a-06`` at six days,
#: ``cohort-a-10``
#: at seven and ``cohort-a-14`` at five. A member searching at the slider's floor sees
#: their own ring at nought kilometres and nobody from the centre, so those three get
#: their depth on the early days her history leaves free instead.
#:
#: **Read down the endings, because they are what the blocks draw.** A pool where every
#: strand publishes 100 is a pool where the Player Score block prints one number on
#: every
#: face and the ladder has one colour in it:
#:
#: - **Two ghosts** — the line-up completed, the evening came and went, nobody said it
#:   had
#:   happened before the entry window shut. It is the one ending that is a *bad* outcome
#:   on
#:   *shows up*, and it is only declarable out here: a ghost needs
#:   :data:`GHOSTED_AT_LEAST_DAYS_AGO` behind it, which is one day more than the whole
#:   week
#:   the layer used to fit inside.
#: - **Two nobody answered** — the score stands by silence, so the square is drawn and
#:   the run keeps its length, and the dock lands on *answers about results* for the two
#:   it was put to. It never lands on **her**: a score is put to the side that did not
#:   enter it, the organiser enters it, and every court out here that she is on is one
#:   she organised — because a court she did not organise has to be a cohort member's
#:   own
#:   ring, and she is in nobody's ring. Her own ignored result comes from her tennis
#:   history, where she is a co-invitee, and this layer leaves it alone.
#: - **One nobody agreed** — an evening and not evidence: it counts toward how much they
#:   have played and produces an outcome for nobody, so *Counted* moves and *Last 5*
#:   does
#:   not. It is the state that makes those two blocks visibly different figures.
THE_RECORD_GOES_BACK: Final[tuple[PlayedGame, ...]] = (
    # -- Ring a, in three groups, because the level gate cuts the ring into three. -----
    #
    # `cohort-a-16` is the ring's middle at 3,17 and organises the middle. It cannot
    # organise the ends: `cohort-a-04` sits at 2,48 and `cohort-a-17` at 3,91, and a
    # search run from the middle returns neither — which the run says out loud rather
    # than leaving to be discovered, because `LEVEL` is a gate and not a sort.
    #
    # So the two ends organise their own, against the faces they are actually near. That
    # is the shape of the whole layer read once more: **a court exists between people
    # the
    # platform would introduce**, and an outlier meets fewer people. Their records are
    # shorter here for the reason they would be shorter in production.
    # The middle.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=3,
        side_a=("cohort-a-16", "cohort-a-06"),
        side_b=("cohort-a-10", "cohort-a-14"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=6,
        side_a=("cohort-a-16", "cohort-a-10"),
        side_b=("cohort-a-05", "cohort-a-13"),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=8,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-13", "cohort-a-12"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=9,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-11", "cohort-a-07"),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=10,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-12", "cohort-a-05"),
        won_by="A",
        answered=False,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=11,
        side_a=("cohort-a-16", "cohort-a-07"),
        side_b=("cohort-a-05", "cohort-a-13"),
        won_by=None,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=12,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-11", "cohort-a-12"),
        won_by="B",
    ),
    # **`cohort-a-04` organises nothing and is on no court, and that is measured.** At
    # 2,48 they are the ring's only Developing face among Established ones, so their own
    # shortlist loses 38 of 52 rows to `LEVEL` and comes back with four — none of them
    # in
    # their ring, and a court here is a ring's own or hers. She cannot see them either.
    #
    # **So they keep an empty record, and it is the right one.** A face the platform
    # would
    # rarely introduce to anybody has little to have watched, which makes them this
    # layer's second measured absence beside `the-newcomer` — one is *too new to have a
    # record*, this one is *too far from everybody to build one*, and the record sheet
    # draws no block row for either. Seating them would have meant relaxing the ring
    # rule
    # until the fixture could assert something the product does not do.
    # **The high end has no court either, and it is the low end's shape upside down.**
    # `cohort-a-17` is Advanced at 3,91 and the ring holds one other, `cohort-a-18`. The
    # two faces below them — `cohort-a-06` and `cohort-a-14`, both at 3,3 — are returned
    # by the search and land **under `QUALITY_FLOOR`**, so the shortlist comes back with
    # seven of fifty-two and three from the ring: themselves, `cohort-a-18` and
    # `cohort-a-08`. Three is one seat short of a padel court, and the missing fourth is
    # the whole of why there is none.
    #
    # It is the more interesting of the two absences, because nothing is *gated*: the
    # people are there, the platform simply will not recommend them to each other. A
    # fixture that forced the court would have been asserting a game the engine declines
    # to arrange.
    # -- `cohort-b-00` is on no court either, and it is `cohort-a-04`'s reason again. --
    #
    # At 2,40 they are the only Developing face in a ring of Established ones, so their
    # own shortlist loses 42 of 52 rows to `LEVEL` and returns three — none of them in
    # their ring. The two faces near enough to organise for them cannot: `cohort-b-01`
    # is
    # the ring's top and never returns them, and `cohort-b-02` declares **FOR_FUN**, so
    # the kind of every court they send is a friendly and a friendly counts toward
    # nothing
    # this sheet draws.
    #
    # **Two isolates and one newcomer, then, and each says a different true thing.** The
    # record sheet needs a face with no block row on it and this layer now supplies
    # three
    # for three reasons, which is better than the one it supplied before.
    # -- `cohort-c-00` and `cohort-d-08`, against her, on singles courts they send. ----
    #
    # **Ring c cannot fill a doubles court for `cohort-c-00`.** Their own shortlist
    # returns
    # one face from their ring — `cohort-c-02`, and that one declares FOR_FUN — while
    # `cohort-c-03` resolves to the fun vector too and `cohort-c-04` is the ring's
    # Advanced outlier at 3,91. What `cohort-c-00` *does* reach on every search is her,
    # which is what `PROTAGONIST_GAMES` already spends three courts proving.
    #
    # So both of them send a **tennis singles** court at her, which is the shape their
    # existing history takes, on the only three days her own calendar leaves free: she
    # has
    # a game on every day from 2 to 27 once the courts above are written, and this layer
    # stops at 30.
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=28,
        side_a=("cohort-c-00",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=29,
        side_a=("cohort-d-08",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=30,
        side_a=("cohort-c-00",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="B",
    ),
    # -- Ring d fills its own, because `cohort-d-05` reaches all of it. ----------------
    #
    # The one ring whose organiser returns the whole of it: `cohort-d-05` sits at 3,20
    # in
    # a ring between 3,14 and 3,31, so nothing here is a level outlier and there was no
    # arrangement to search for.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=13,
        side_a=("cohort-d-05", "cohort-d-08"),
        side_b=("cohort-d-04", "cohort-d-07"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=15,
        side_a=("cohort-d-05", "cohort-d-08"),
        side_b=("cohort-d-07", "cohort-d-04"),
        won_by="B",
    ),
    # **Ring d gets three clean courts and neither bad ending, and that is a constraint
    # rather than a preference.** Every face `cohort-d-05` can see is one of the tennis
    # opponents `PLAYED_GAMES` already spends — `cohort-d-01`, `-02`, `-04`, `-07`,
    # `-08`
    # — and a ghost here costs *shows up* thirty-five points of a published blend, which
    # is enough to drop that person under `QUALITY_FLOOR` on the tennis search the
    # cohort
    # arranges those very games from. It did: `cohort-a-12`'s search stopped returning
    # `cohort-d-01`, and the cohort's own history refused to write.
    #
    # It is worth reading twice, because it is the fixture demonstrating the product. A
    # bad record **does** cost somebody games, and this layer is close enough to the
    # engine to make that visible by accident. Variety here is bought where it costs
    # nobody a court they were already promised.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=17,
        side_a=("cohort-d-05", "cohort-d-04"),
        side_b=("cohort-d-08", "cohort-d-07"),
        won_by="B",
    ),
    # -- Hers, one a day, oldest last. ------------------------------------------------
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=12,
        side_a=(PROTAGONIST_HANDLE, "in-your-line-up-and-accepted"),
        side_b=("they-challenged-you", "you-challenged-them"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=13,
        side_a=(PROTAGONIST_HANDLE, "said-yes-to-you"),
        side_b=("the-one-sport-player", "they-turned-down-your-court"),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=14,
        side_a=(PROTAGONIST_HANDLE, "you-passed-them"),
        side_b=("your-yes-makes-it-mutual", "you-said-yes-to-them"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=15,
        side_a=(PROTAGONIST_HANDLE, "in-your-line-up-still-deciding"),
        side_b=("cohort-a-13", "cohort-a-12"),
        won_by="B",
    ),
    # **The first ghost.** Nobody claimed the evening and the entry window closed over
    # it.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=16,
        side_a=(PROTAGONIST_HANDLE, "they-challenged-you"),
        side_b=("in-your-line-up-and-accepted", "you-passed-them"),
        won_by=None,
        entered=False,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=17,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-05"),
        side_b=("cohort-a-07", "cohort-a-13"),
        won_by="A",
    ),
    # **Nobody answered.** The score stands, and the two opposite carry an ignored
    # result.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=18,
        side_a=(PROTAGONIST_HANDLE, "the-one-sport-player"),
        side_b=("said-yes-to-you", "you-challenged-them"),
        won_by="B",
        answered=False,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=19,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-07"),
        side_b=("cohort-a-11", "cohort-a-16"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=20,
        side_a=(PROTAGONIST_HANDLE, "your-yes-makes-it-mutual"),
        side_b=("you-passed-them", "they-turned-down-your-court"),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=21,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-12"),
        side_b=("cohort-a-05", "cohort-a-16"),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=22,
        side_a=(PROTAGONIST_HANDLE, "you-said-yes-to-them"),
        side_b=("in-your-line-up-still-deciding", "in-your-line-up-and-accepted"),
        won_by="B",
    ),
    # **Nobody answered**, a second time, so the dock is not one person's accident.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=23,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-13"),
        side_b=("cohort-a-11", "cohort-a-16"),
        won_by="A",
        answered=False,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=24,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-11"),
        side_b=("cohort-a-05", "cohort-a-13"),
        won_by="B",
    ),
    # **The one nobody agreed.** An evening and not evidence: *Counted* moves and
    # *Last 5* does not, which is what makes the two blocks different figures on a face.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=25,
        side_a=(PROTAGONIST_HANDLE, "cohort-a-07"),
        side_b=("they-challenged-you", "you-challenged-them"),
        won_by=None,
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=26,
        side_a=(PROTAGONIST_HANDLE, "said-yes-to-you"),
        side_b=("in-your-line-up-and-accepted", "in-your-line-up-still-deciding"),
        won_by="A",
    ),
    # **The second ghost**, on a different court, so *shows up* is not one pair's story.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=27,
        side_a=(PROTAGONIST_HANDLE, "you-said-yes-to-them"),
        side_b=("they-challenged-you", "the-one-sport-player"),
        won_by=None,
        entered=False,
    ),
)

#: The whole layer, as the runner writes it. **The rateable week first**, because the
#: order here is the order the games are written in and the older courts are the ones a
#: search can afford to fail on last.
THE_POOL_HAS_A_RECORD: Final[tuple[PlayedGame, ...]] = (
    *THE_RATEABLE_WEEK,
    *THE_RECORD_GOES_BACK,
)

#: What the people on those courts said about each other. Declared here rather than
#: beside the cohort's own table for the reason the resolver is: half of these subjects
#: are not cohort members, and a refusal has to see everybody it is asked about.
#:
#: **Varied on purpose and thin on purpose.** A pool where every figure is 5,0 over one
#: rater teaches a reader nothing about the field, and one where everybody has rated
#: everybody is a population nobody will ever meet — so the counts run one to three, the
#: figures span the scale, and two faces keep a record with **no** stars, which is the
#: commonest state there is.
WHAT_THE_POOL_SAID: Final[Mapping[str, Mapping[str, int]]] = {
    "cohort-a-05": {PROTAGONIST_HANDLE: 4, "cohort-a-07": 5},
    "cohort-a-06": {"cohort-a-16": 3, "cohort-a-10": 4},
    "cohort-a-07": {
        PROTAGONIST_HANDLE: 5,
        "cohort-a-05": 4,
        "the-one-sport-player": 5,
    },
    "cohort-a-10": {"cohort-a-06": 4},
    "cohort-a-11": {"cohort-a-16": 5},
    "cohort-a-13": {PROTAGONIST_HANDLE: 3, "you-said-yes-to-them": 2},
    "the-one-sport-player": {PROTAGONIST_HANDLE: 2, "cohort-a-07": 3},
    "said-yes-to-you": {PROTAGONIST_HANDLE: 5},
    "you-passed-them": {PROTAGONIST_HANDLE: 1},
    "you-said-yes-to-them": {PROTAGONIST_HANDLE: 4, "cohort-a-13": 5},
    "your-yes-makes-it-mutual": {PROTAGONIST_HANDLE: 5, "said-yes-to-you": 4},
}


def _refuse_a_pool_history_nobody_could_play() -> None:
    """Every row, against the three populations that supply its seats.

    Most of what is checked is that the list stayed inside the world as drawn: a face
    that is nobody, a game before its player existed, two courts on one evening. Each
    would otherwise surface mid-run as a message about a pool, blaming the search
    rather than the row.
    """

    known = {member.handle: member.committed_days_ago for member in COHORT.members}
    for slug, account in NAMED_ACCOUNTS.items():
        if account.profile is not None:
            known[slug] = account.profile.committed_days_ago

    days: dict[str, set[int]] = {}
    for game in (*PLAYED_GAMES, *PROTAGONIST_GAMES):
        for handle in game.players:
            days.setdefault(handle, set()).add(game.played_days_ago)

    for index, game in enumerate(THE_POOL_HAS_A_RECORD):
        organiser = game.organiser
        # **A court is hers, a ring's own, or a cohort member's against her**, and the
        # third arm is the second one's argument rather than an exception to it. What
        # the
        # ring rule is really asserting is *this organiser's shortlist provably returns
        # these seats*; a cohort member reaching the protagonist is the one other thing
        # this fixture already proves, in `PROTAGONIST_GAMES`, where every row is a
        # member
        # organising a singles court against her. Ring c is why it is needed:
        # `cohort-c-00`
        # reaches exactly one face in their own ring and cannot fill a doubles court
        # with
        # it, and reaches her on every search they run.
        if organiser != PROTAGONIST_HANDLE and set(game.players[1:]) != {
            PROTAGONIST_HANDLE
        }:
            # **The one alternative that works.** A member searching at the slider's
            # floor sees their own ring at nought kilometres and nobody from the
            # centre, so the shortlist cannot fill before it reaches three named
            # people. Any other organiser has to cross to the centre, and a radius that
            # wide fills twenty rows with accounts no fixture named.
            ring = organiser.split("-")[1] if organiser.startswith("cohort-") else None
            strangers = [
                handle
                for handle in game.players[1:]
                if not handle.startswith("cohort-") or handle.split("-")[1] != ring
            ]
            if ring is None or strangers:
                raise RuntimeError(
                    f"pool game {index} is organised by '{organiser}' and seats "
                    f"{strangers}. A court here is either hers — the one search "
                    f"that provably returns the whole pool — or one cohort "
                    f"member's own ring, which is the only other shortlist that "
                    f"cannot fill before it finds everybody named."
                )
        if THE_NEWCOMER.slug in game.players:
            raise RuntimeError(
                f"pool game {index} seats '{THE_NEWCOMER.slug}', who committed "
                f"days ago inside the newcomer window. A brand-new account with a "
                f"record is a lie about how a record accumulates — and it is the "
                f"absent card this pool still owes `screens.py`, which after this "
                f"layer has no other."
            )
        if game.played_days_ago < PLAYED_AT_LEAST_DAYS_AGO:
            raise RuntimeError(
                f"pool game {index} was played {game.played_days_ago} day(s) ago "
                f"and a seeded result needs {PLAYED_AT_LEAST_DAYS_AGO}."
            )
        rateable = game in THE_RATEABLE_WEEK
        if rateable and game.played_days_ago > RATED_WITHIN_DAYS:
            raise RuntimeError(
                f"rateable pool game {index} was played {game.played_days_ago} "
                f"day(s) ago, past the card's own {RATED_WITHIN_DAYS}-day week. "
                f"That list is the half of this layer that buys **stars**, and a "
                f"court nobody may be asked about buys none — move it to "
                f"`THE_RECORD_GOES_BACK`, which is where a court that buys only a "
                f"record belongs."
            )
        if game.played_days_ago > THE_RECORD_GOES_BACK_DAYS:
            raise RuntimeError(
                f"pool game {index} was played {game.played_days_ago} day(s) ago, "
                f"past this layer's own {THE_RECORD_GOES_BACK_DAYS}-day bound. The "
                f"bound is where the *next* refusal would start firing instead — a "
                f"game may not predate the profile of somebody who played it, and "
                f"the named accounts commit at forty — so a court beyond it fails "
                f"naming a member rather than naming the reach of the fixture."
            )
        # **A ghost is only a ghost once the clock says so**, and out here it can be
        # declared at all: the entry window has to have closed on silence, which needs
        # one more day than the whole week `THE_RATEABLE_WEEK` fits inside. A typed
        # ghost inside the week would read as `AWAITING_ENTRY` and publish *shows up*
        # over a denominator it never entered — which is exactly the defect a typed
        # seven produced in `cohort.py` before the constant was derived.
        if game.was_a_ghost and game.played_days_ago < GHOSTED_AT_LEAST_DAYS_AGO:
            raise RuntimeError(
                f"pool game {index} is declared a ghost {game.played_days_ago} "
                f"day(s) ago, and a plan is a ghost only once its entry window has "
                f"closed — {GHOSTED_AT_LEAST_DAYS_AGO} day(s). Sooner than that the "
                f"platform still calls it `AWAITING_ENTRY`, so nothing would fail "
                f"and the record would simply be wrong."
            )
        if len(set(game.players)) != len(game.players):
            raise RuntimeError(f"pool game {index} seats somebody twice")

        for handle in game.players:
            address_of(handle)
            committed = known.get(handle)
            if committed is None:
                raise RuntimeError(
                    f"pool game {index} seats '{handle}', who holds no profile — "
                    f"so there is nobody for a search to return and no court to "
                    f"seat them on."
                )
            if committed <= game.played_days_ago:
                raise RuntimeError(
                    f"pool game {index} was played {game.played_days_ago} day(s) "
                    f"ago and '{handle}' committed their profile {committed} "
                    f"day(s) ago — a game before the player existed."
                )
            if game.played_days_ago in days.setdefault(handle, set()):
                raise RuntimeError(
                    f"'{handle}' plays twice on the same day, and *Last 5* is "
                    f"ordered on the instant each game was played."
                )
            days[handle].add(game.played_days_ago)


def _refuse_an_opinion_nobody_was_on_a_court_to_have() -> None:
    """Every declared rating, against the courts this layer writes.

    The cohort's own table one file over is held to the same rule, asked about a
    narrower population: a card is drawn for an evening that happened and is over, so a
    rating with no court behind it is one the use case would refuse mid-run.
    """

    lowest, highest = STARS_ARE_ONE_TO_FIVE
    together: dict[str, set[str]] = {}
    # **The rateable week and never the whole layer.** A card is drawn for an evening
    # that happened, is over, and is still inside its own seven days — so a rating
    # declared on one of the older courts is one the use case would refuse mid-run, and
    # widening this walk to `THE_POOL_HAS_A_RECORD` is how that stops being caught here.
    for game in THE_RATEABLE_WEEK:
        if game.was_a_ghost:
            continue
        for pair in game.pairs:
            one, other = sorted(pair)
            together.setdefault(one, set()).add(other)
            together.setdefault(other, set()).add(one)

    for subject, said in WHAT_THE_POOL_SAID.items():
        for rater, stars in said.items():
            if rater == subject:
                raise RuntimeError(f"'{subject}' rates themselves.")
            if not lowest <= stars <= highest:
                raise RuntimeError(
                    f"'{rater}' gives '{subject}' {stars} star(s), and a tap is "
                    f"{lowest} to {highest}. There is no nought."
                )
            if rater not in together.get(subject, set()):
                raise RuntimeError(
                    f"'{rater}' rates '{subject}' and the two of them share no "
                    f"court in `THE_RATEABLE_WEEK`. A card is drawn for an "
                    f"evening that is over and still inside its own week."
                )


_refuse_a_pool_history_nobody_could_play()
_refuse_an_opinion_nobody_was_on_a_court_to_have()

__all__ = [
    "NAMED_ACCOUNTS",
    "THE_POOL_HAS_A_RECORD",
    "THE_RATEABLE_WEEK",
    "THE_RECORD_GOES_BACK",
    "THE_RECORD_GOES_BACK_DAYS",
    "WHAT_THE_POOL_SAID",
    "address_of",
    "handle_of",
]
