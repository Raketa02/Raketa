"""The seed path: what it may not do, what it writes, and that the command runs.

Four claims, and each fails differently.

1. **Nothing in the seed path writes a table directly** — a structural walk,
   because that is the failure this system exists to prevent and a green suite
   would look identical afterwards. An `INSERT` into `users` produces an account
   that signs in perfectly and has no event stream behind it; the seeded data and
   the system's own account of that data then disagree, and only a replay ever
   says so. The same walk is what states *no aggregate is invented for a context
   that is not yet modeled*: the seed path writes only the contexts listed in
   `WRITTEN_CONTEXTS`, and a context joins that list on the day it exists.
2. **Every account is named for a state, and the name is checked.** The
   catalog's own refusals fire before a session is opened; the runner's fire
   against the rating that is stored, so an engine retune that moves
   `rating-barely-established` out of its band stops the seed instead of quietly
   renaming a player.
3. **The aggregates it creates have real event streams, and a second run leaves
   them alone** — asserted by reading the store, which is the one place the
   answer is not a matter of opinion. That the streams *replay* is
   `tests/api/test_seeds.py`'s, through the API, because a replay is only
   interesting where something depends on it.
4. **The command itself runs** — `python -m app.seeds`, twice, against a real
   database file. A seed system nobody has invoked from a shell is a library.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.bootstrap.composition import (
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_skill_rating_repository,
    build_user_repository,
)
from app.engines.assessment import AnswerOption, Question
from app.infrastructure.database.base import Base
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
from app.modules.auth.presentation.schemas import LoginRequest
from app.modules.users.domain.value_objects import Email, Nickname, RawPassword
from app.modules.users.presentation.schemas import UserResponse
from app.seeds import catalog
from app.seeds.catalog import (
    ACCOUNTS,
    BAND_ESTABLISHED,
    NICKNAMES,
    RESERVED_TLD,
    SEED_EMAIL_DOMAIN,
    SEED_PASSWORD,
    AbandonedRun,
    AnswerPolicy,
    OpenRun,
    RatedRun,
    RatingClaim,
    SeedAccount,
)
from app.seeds.runner import (
    SeededAccount,
    SeededScenario,
    SeedFailed,
    SeedReport,
    report,
    seed,
)
from tests.unit.bcrypt_cost import BCRYPT_MINIMUM_ROUNDS

ROOT = Path(__file__).resolve().parents[2]

#: Every module in the seed path. A glob, so a file added tomorrow is walked on
#: the day it exists — and the count is asserted rather than trusted, because a
#: glob that matches nothing passes silently and reads as a rule that held.
SEED_MODULES = sorted((ROOT / "app" / "seeds").glob("*.py"))

#: The four TLDs RFC 2606 §2 reserves, in one sentence, forever. No registry
#: will sell a name under any of them.
RFC2606_RESERVED_TLDS = frozenset({".test", ".example", ".invalid", ".localhost"})

#: The contexts the seed path **writes an aggregate in**. Courts, Bookings and
#: Matches are modeled nowhere, so a seed for one of them would have to invent
#: the aggregate first.
#:
#: `challenges` and `blocks` joined on the day the relationship layer landed, as
#: *writes through their own use cases*, and left with it (#578): the layer sent
#: challenges, and a context that no longer exists is written by nothing.
#:
#: `conversations` joined for one act rather than for the rooms. The seed opens
#: no room and cannot: a room is *told*, through the outbox, by contexts that do
#: not know it exists, so the fixture drains the queue and the rooms appear. What
#: it does write is the one thing a room cannot be told — somebody saying
#: something — through `SendMessage`, because a room long enough to page backward
#: through is a screen state and no arrangement produces one.
#:
#: `plans` joined the ordinary way, three slot writes through their use cases,
#: and left with the context (#578).
#:
#: `clubs` joined on the day the Club context was written (#503), and it is the
#: first context this rule *waited for* rather than one it admitted: the list
#: below used to name Clubs as the example of a context modeled nowhere. A club
#: exists because a club signed up (`docs/adr/0182` §7), so the seed signs each
#: one up through `SignUpClub` and writes no row.
#:
#: `groups` joined the day after (#504), the same way: a group exists because a
#: player created it, so each is created through `CreatePlayerGroup` and joined
#: through `JoinGroup`, and the projections are the repository's to write.
#:
#: `friends` and `blocks` joined with #745: friendships asked and answered
#: through their use cases, and one block through `BlockPlayer`, whose delivery
#: ends the friendship it stands between.
WRITTEN_CONTEXTS = frozenset(
    {
        "administrators",
        "auth",
        "clubs",
        "groups",
        "users",
        "rating",
        "player_profile",
        "games",
        "conversations",
        "payments",
        "proposals",
        "friends",
        "blocks",
    }
)

#: The contexts the seed path only **exercises**, through their own use cases.
#: The assertions run real searches, deal real decks and compose real line-ups,
#: and those use cases write the module's own durable ledgers — a search record,
#: an interest row — which is not the same act as seeding an aggregate.
#:
#: `sportsmanship` joined on the day the record sheet needed *what other players
#: said* to be non-empty, and it joined **here** rather than above for a reason
#: the context chose: a card is not event-sourced and there is no aggregate to
#: write. `AnswerTheCard` writes that module's own two tables through its own
#: unit of work, which is the same shape as a search record.
#:
#: `rankings` joined with #768, and it has no aggregate at all: its rows are
#: folded from the rating streams by the outbox delivery, so the seed only
#: **reads** the list, through the page's own use case, to prove it.
#:
#: `discovery` joined with #793 on the same terms: its player directory is
#: written by the outbox delivery from the users' and the profiles' events, so
#: the seed only **reads** New in Rakieta, through the row's own use case.
EXERCISED_CONTEXTS = frozenset(
    {"discovery", "matchmaking", "rankings", "sportsmanship"}
)

#: The repository builders the seed path may take from the composition root, and
#: the context each of them writes an aggregate in. Written out by name, because
#: a builder is how an aggregate is written and the **name** is often the only
#: place the context appears — a use case takes its repository from here and
#: never imports the port, so a builder nobody listed is a write nothing in this
#: file would notice.
AGGREGATE_WRITERS = {
    "build_user_repository": "users",
    "build_assessment_repository": "rating",
    "build_skill_rating_repository": "rating",
    "build_player_profile_repository": "player_profile",
    "build_play_intent_declaration_repository": "player_profile",
    # The played history states and answers a result, which is `games`' own
    # aggregate written through `games`' own two use cases. The **game** itself
    # is opened by the last yes that booked it, inline and inside `proposals`,
    # so nothing here opens one.
    "build_game_repository": "games",
    # The messages, and **not the rooms**. A room is opened and grown by the
    # outbox delivering somebody else's events, which needs no repository from
    # this file at all; the repository is here because `SendMessage` takes one,
    # and a seeded bubble goes through the use case a request runs like
    # everything else.
    "build_conversation_repository": "conversations",
    # The club and its account, both written by the one `SignUpClub` a desk
    # runs — which is why the layer needs both, and nothing else.
    "build_club_repository": "clubs",
    "build_club_account_repository": "clubs",
    # What each club offers Rakieta — courts, hours, an exception, prices and
    # how it works — written by the use cases the club website's Courts &
    # prices and Rakieta settings run (#535), one stream per club.
    "build_club_courts_repository": "clubs",
    # A group, created by its Owner and joined by its members — the two use
    # cases a request runs, over the one repository both take.
    "build_group_repository": "groups",
    # The games still filling: a pick made by `MakeProposal` — the use case the
    # engine will drive (#540) — and its yeses said by `SayYes`, the swipe's own
    # use case, over the one repository both take (#538). **The last yes books
    # the game** (#541): the booking, its Game and every seat's charge are
    # written inline by that same `SayYes` — so `app/seeds/bookings.py` takes no
    # repository of its own.
    "build_proposal_repository": "proposals",
    # An Administrator, invited by its club and let in the way that person
    # would get in — `InviteAdministrator`, then `SetInvitationPassword` or
    # `AcceptInvitation` — over the one repository all three take.
    "build_administrator_repository": "administrators",
    # The session setting a password signs in: `SetInvitationPassword` answers
    # a signed-in pair, as the request it is does, and that pair is a refresh
    # token row written through `auth`'s own `TokenRotator`.
    "build_refresh_token_repository": "auth",
    # A player's saved card, set up the way a phone sets it up — start, the
    # terms, the save — over the one repository all three take (#536).
    "build_payment_method_repository": "payments",
    # Friendships asked, accepted and set aside through `AskToBeFriends`,
    # `AcceptFriendRequest` and `SetAsideFriendRequest`, over the one repository
    # all three take (#745).
    "build_friendship_repository": "friends",
    # The friends layer's block case: one player blocks another through
    # `BlockPlayer`, the block route's own use case, so the friendship ends as a
    # block's delivery ends it (#745, `docs/adr/0202` §2).
    "build_block_repository": "blocks",
}

#: The two infrastructure modules the seed path may import, and neither is an
#: adapter: both are the **process's own connection**, which is the same
#: allowance `presentation/dependencies.py` has for `get_db` and `get_redis`.
#: `redis_client.py` says so in its own docstring — *nothing here knows what a
#: ledger is* — and the ledgers built over the client come from the composition
#: root with their fail-soft posture already on them.
PROCESS_CONNECTIONS = ("database.engine", "infrastructure.redis_client")

#: SQLAlchemy's statement constructors. Importing one into the seed path is how
#: "just this once, it is only a fixture row" starts.
SQL_CONSTRUCTORS = frozenset(
    {"select", "insert", "update", "delete", "text", "table", "column"}
)

#: What a session is called here — `build_user_repository(session)` is the only
#: thing the seed path does with one.
SESSION_NAMES = frozenset({"session", "db", "conn", "connection"})

#: Session methods that reach a table. Matched against a *receiver* rather than
#: bare, because `execute` is also what a use case is asked to do — and asking a
#: use case to execute is the entire point of this package.
SESSION_WRITES = frozenset(
    {"add", "add_all", "merge", "delete", "execute", "scalars", "flush"}
)


def imported(path: Path) -> set[tuple[str, str]]:
    """`(module, name)` for every import in the file, `import x` included."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update((alias.name, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.update((node.module, alias.name) for alias in node.names)
    return found


def session_calls(path: Path) -> set[str]:
    """Every `session.method(...)` called in the file, by receiver name."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        f"{node.func.value.id}.{node.func.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in SESSION_NAMES
        and node.func.attr in SESSION_WRITES
    }


def a_question(*, tier: str | None, options: int) -> Question:
    """A question shaped like the bank's, with options weakest-first."""

    return Question(
        id="probe",
        category="Probe",
        situation="A situation.",
        text="A question?",
        qualifier="Choose one.",
        tier=tier,
        options=tuple(
            AnswerOption(id=f"o{index}", text=f"option {index}")
            for index in range(options)
        ),
    )


# ---------------------------------------------------------------------------
# 1. No direct table writes, and no context that does not exist
# ---------------------------------------------------------------------------


def test_the_walk_has_something_to_walk():
    """The lesson a wildcard fence paid for: a glob matching nothing is a rule
    that holds vacuously and reads exactly like one that holds."""

    names = {path.name for path in SEED_MODULES}
    assert names == {
        "__init__.py",
        "__main__.py",
        "administrators.py",
        "booked_history.py",
        "bookings.py",
        "catalog.py",
        "clock.py",
        "club_courts.py",
        "clubs.py",
        "cohort.py",
        "for_fun.py",
        "friends.py",
        "friends_games.py",
        "full_hour.py",
        "groups.py",
        "guard.py",
        "hottest_groups.py",
        "money.py",
        "new_in_rakieta.py",
        "official_groups.py",
        "payments.py",
        "photos.py",
        "posts.py",
        "proposals.py",
        "ranking_crowd.py",
        "rankings.py",
        "rescues.py",
        "rooms.py",
        "runner.py",
        "same_level.py",
        "same_vibe.py",
        "screens.py",
        "sportsmanship.py",
        "top_ten.py",
    }


@pytest.mark.parametrize("path", SEED_MODULES, ids=lambda p: p.name)
def test_no_seed_module_imports_an_orm_model_or_a_statement(path):
    for module, name in imported(path):
        assert "infrastructure.database.models" not in module, path.name
        assert not module.endswith("_model"), path.name
        assert ".infrastructure" not in module or module.endswith(
            PROCESS_CONNECTIONS
        ), f"{path.name} imports an adapter's internals: {module}"
        if module == "sqlalchemy" or module.startswith("sqlalchemy."):
            assert name not in SQL_CONSTRUCTORS, f"{path.name} imports {name}"


@pytest.mark.parametrize("path", SEED_MODULES, ids=lambda p: p.name)
def test_no_seed_module_writes_through_a_session(path):
    """`session.add(...)` is the one-line version of the thing this system
    exists to refuse — and it is a line that works.

    Matched on the receiver's name, which is what the codebase calls a session.
    That is narrower than it sounds: reaching a table under another name means
    importing a statement or an ORM model, and the walk above refuses both.
    """

    offending = session_calls(path)
    assert not offending, f"{path.name} calls {sorted(offending)}"


def test_the_seed_path_touches_only_the_contexts_that_exist():
    """*No aggregate is invented for a context that is not yet modeled*, stated
    as **writes against reads** rather than as imports.

    The rule used to be *the seed path imports `users` and `rating` and nothing
    else*, and that stopped being able to fail on the day the assertions arrived:
    reading a screen means running matchmaking's own use cases, so the import
    appears whatever the seed does with it. Worse, as an import check it would
    have gone green the day somebody wrote a matchmaking **aggregate** from the
    seed — the import was already there.

    So the fence is the distinction that actually matters. The seed **writes**
    aggregates in `users`, `rating` and `player_profile`, and it reaches every
    other context through that context's own use cases. A repository is how an
    aggregate is written, so a repository port — or a repository builder — from
    anywhere else is the line being crossed, and it is refused by name.

    Writing a matchmaking **aggregate** would need a matchmaking repository, and
    there is not one to import; the day somebody writes one, the builder check
    above is what fails. (The matchmaking ledgers the seed once imported went
    with the searches, #579.)

    Equality in both directions, on purpose. A Courts repository appearing is the
    scope creep the rule forbids; `rating` *disappearing* is the seed quietly
    reducing to a list of registrations, which is the state this catalog grew out
    of.
    """

    imports = [
        (module, name) for path in SEED_MODULES for module, name in imported(path)
    ]

    builders = {
        name
        for module, name in imports
        if module == "app.bootstrap.composition" and name.endswith("_repository")
    }
    assert builders <= set(AGGREGATE_WRITERS), sorted(
        builders - set(AGGREGATE_WRITERS)
    )

    written = {
        module.split(".")[2]
        for module, name in imports
        if module.startswith("app.modules.") and name.endswith("Repository")
    } | {AGGREGATE_WRITERS[name] for name in builders}
    assert written == WRITTEN_CONTEXTS

    contexts = {
        module.split(".")[2]
        for module, _ in imports
        if module.startswith("app.modules.")
    }
    assert contexts == WRITTEN_CONTEXTS | EXERCISED_CONTEXTS


# ---------------------------------------------------------------------------
# 2. The catalog: named states, and names that are checked
# ---------------------------------------------------------------------------


def test_every_address_is_on_a_reserved_tld():
    """The point of the rule is that no registry can ever sell the name.

    `RFC2606_RESERVED_TLDS` is written out here rather than read from the
    catalog, because a test that checks a constant against itself agrees with
    every value that constant could take — a mutation run put that hole here,
    and `.com` passed. Which of the four is used, and why it is not `.test`, is
    `test_the_boundary_schemas_accept_every_seeded_address`.
    """

    assert RESERVED_TLD in RFC2606_RESERVED_TLDS
    assert SEED_EMAIL_DOMAIN.endswith(RESERVED_TLD)
    for account in ACCOUNTS:
        assert account.email.endswith(RESERVED_TLD)


def test_every_account_is_addressed_by_its_state_and_shown_under_a_nickname():
    """**The slug addresses the account; it is never what a person sees.**

    The two were one string, and a screen draws the nickname — so the builder
    was printing *said-yes-to-you* where a person goes, and a developer could
    not tell a court full of people from a list of test conditions. Splitting
    them keeps the address derived from the state, so an account still cannot
    be called one thing and reachable at another.

    The nickname is asserted to be a **dealt** one rather than merely
    different, because `nickname` falls back to the slug for accounts a guard
    builds to refuse: this is the test that the fallback never reaches a real
    one.
    """

    for account in ACCOUNTS:
        assert account.email == f"{account.slug}@{SEED_EMAIL_DOMAIN}"
        assert account.nickname == NICKNAMES[account.slug]
        assert account.nickname != account.slug
        assert account.description


def test_every_account_is_a_lowercase_handle_and_holds_no_name():
    """``first_last``, spelled as a handle (``docs/adr/0199`` §1): the seeded
    court reads *diego_fabregat left*. **The catalogue holds no player name** —
    nothing on an account spells one."""

    for account in ACCOUNTS:
        first, last = account.nickname.split("_")
        assert first and last and account.nickname == account.nickname.lower()
        assert not hasattr(account, "name")


def test_the_catalog_covers_the_states_a_screen_has_to_render():
    """The edges, named: nothing yet, one open, one failed, one just rated, a
    rating at the edge of its band and one well inside it, and the maximum.

    Asserted as *properties of the accounts* rather than as a list of slugs, so
    a rename is free and deleting a state is not.
    """

    by_slug = {account.slug: account for account in ACCOUNTS}

    assert by_slug["brand-new-player"].scenarios == ()
    assert [type(s) for s in by_slug["assessment-in-progress"].scenarios] == [OpenRun]
    assert [type(s) for s in by_slug["assessment-abandoned"].scenarios] == [
        AbandonedRun
    ]
    assert [type(s) for s in by_slug["assessment-completed"].scenarios] == [RatedRun]

    barely = by_slug["rating-barely-established"].scenarios[0]
    well = by_slug["rating-well-established"].scenarios[0]
    assert isinstance(barely, RatedRun) and isinstance(well, RatedRun)
    # The same band, which is what makes the pair worth having: the difference
    # is where in it they sit, and nothing else.
    assert barely.claim.band == well.claim.band == BAND_ESTABLISHED
    assert barely.claim.position[1] <= well.claim.position[0]

    every_sport = by_slug["rated-in-every-sport"]
    assert {scenario.sport for scenario in every_sport.scenarios} == set(Sport)
    bands = [
        scenario.claim.band
        for scenario in every_sport.scenarios
        if isinstance(scenario, RatedRun)
    ]
    assert len(bands) == len(set(bands)) == len(Sport), "two sports in one band"


def test_the_catalog_is_addressable_by_the_domain():
    """The values the registration endpoint would be handed, asked of the same
    value objects it validates them with."""

    RawPassword(SEED_PASSWORD)
    for account in ACCOUNTS:
        assert Email(account.email).value == account.email
        assert Nickname(account.nickname).value == account.nickname


def test_an_unaddressable_catalog_is_refused_before_anything_is_written(
    monkeypatch,
):
    """The check runs at import, so a bad entry never reaches a half-done run.

    What this pins is that the check *works*; that it is *called* on import is
    not separately asserted, and removing the call alone leaves this suite green
    — every property it enforces is asserted directly above. The call is what
    turns a mid-run failure into a legible one, not the only thing standing
    between the catalog and a bad address.
    """

    monkeypatch.setattr(
        catalog,
        "ACCOUNTS",
        (SeedAccount(slug="a", description="too short"),),
    )

    with pytest.raises(ValueError, match="name"):
        catalog._refuse_an_impossible_catalog()


def test_two_scenarios_for_one_sport_are_refused(monkeypatch):
    """A state the domain cannot reach, caught before the run that fails on it.

    A rated sport refuses a second assessment, so an account with two padel
    scenarios does not fail at import for tidiness — it fails three quarters of
    the way through a seed run, with five accounts already written.
    """

    monkeypatch.setattr(
        catalog,
        "ACCOUNTS",
        (
            SeedAccount(
                slug="two-runs-one-sport",
                description="impossible",
                scenarios=(OpenRun(sport=Sport.PADEL), AbandonedRun(sport=Sport.PADEL)),
            ),
        ),
    )

    with pytest.raises(RuntimeError, match="two scenarios for PADEL"):
        catalog._refuse_an_impossible_catalog()


@pytest.mark.parametrize(
    ("scenario", "complaint"),
    [
        (
            RatedRun(
                sport=Sport.PADEL,
                answers=AnswerPolicy(claims=-1, demonstrations=0),
                claim=RatingClaim(band=BAND_ESTABLISHED),
            ),
            "index into the options",
        ),
        (
            RatedRun(
                sport=Sport.PADEL,
                answers=AnswerPolicy(claims=2, demonstrations=2),
                claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.8, 0.2)),
            ),
            "read low to high",
        ),
        (
            RatedRun(
                sport=Sport.PADEL,
                answers=AnswerPolicy(claims=2, demonstrations=2),
                claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.0, 1.5)),
            ),
            "not a fraction",
        ),
    ],
    ids=["negative-index", "backwards-position", "position-off-the-band"],
)
def test_a_scenario_that_cannot_mean_anything_is_refused(
    monkeypatch, scenario, complaint
):
    monkeypatch.setattr(
        catalog,
        "ACCOUNTS",
        (SeedAccount(slug="nonsense", description="nonsense", scenarios=(scenario,)),),
    )

    with pytest.raises(RuntimeError, match=complaint):
        catalog._refuse_an_impossible_catalog()


def test_an_answer_policy_reads_the_split_off_the_ports_own_vocabulary():
    """`tier` is the abstraction's marker for a demonstration question — set for
    execution questions, `None` otherwise — so the policy needs no question id."""

    policy = AnswerPolicy(claims=1, demonstrations=3)

    claim = a_question(tier=None, options=5)
    demonstration = a_question(tier="standard", options=5)

    assert policy.option_id_for(claim, drawn_for="named") == "o1"
    assert policy.option_id_for(demonstration, drawn_for="named") == "o3"


def test_an_answer_policy_clamps_to_the_options_a_question_offers():
    """The bank's questions carry four options or five. A policy is a strength,
    not an index that has to know which."""

    policy = AnswerPolicy(claims=4, demonstrations=4)

    claim = a_question(tier=None, options=4)
    demonstration = a_question(tier="basic", options=5)

    assert policy.option_id_for(claim, drawn_for="named") == "o3"
    assert policy.option_id_for(demonstration, drawn_for="named") == "o4"


def test_a_claim_is_silent_about_a_rating_that_matches_it():
    claim = RatingClaim(band=BAND_ESTABLISHED, position=(0.0, 0.25))

    assert (
        claim.complaint_about(
            band_name=BAND_ESTABLISHED, level=2.86, band_lower=2.7, band_upper=3.8
        )
        is None
    )


def test_a_claim_names_the_band_it_expected_and_the_one_it_found():
    claim = RatingClaim(band=BAND_ESTABLISHED)

    complaint = claim.complaint_about(
        band_name="Developing", level=2.4, band_lower=1.6, band_upper=2.6
    )

    assert complaint is not None
    assert "Developing" in complaint and BAND_ESTABLISHED in complaint


def test_a_claim_refuses_a_level_in_the_right_band_and_the_wrong_part_of_it():
    """What tells `barely` from `well`. Without it the two accounts are one
    account with two addresses."""

    barely = RatingClaim(band=BAND_ESTABLISHED, position=(0.0, 0.25))

    complaint = barely.complaint_about(
        band_name=BAND_ESTABLISHED, level=3.66, band_lower=2.7, band_upper=3.8
    )

    assert complaint is not None
    assert "87%" in complaint


def test_a_claim_reads_the_bands_edges_off_the_rating_it_is_given():
    """The edges travel *on* the rating, so a re-cut band moves the claim with
    it: the same Level is barely inside a band that starts just under it and
    well inside one that starts far below."""

    barely = RatingClaim(band=BAND_ESTABLISHED, position=(0.0, 0.25))

    assert (
        barely.complaint_about(
            band_name=BAND_ESTABLISHED, level=2.86, band_lower=2.7, band_upper=3.8
        )
        is None
    )
    assert (
        barely.complaint_about(
            band_name=BAND_ESTABLISHED, level=2.86, band_lower=2.0, band_upper=3.0
        )
        is not None
    )


def test_the_boundary_schemas_accept_every_seeded_address():
    """The domain is not the only thing with an opinion about an address.

    `LoginRequest` and `UserResponse` are `pydantic.EmailStr`, which refuses any
    TLD on `email-validator`'s special-use list — `.test` among them. That is why
    `RESERVED_TLD` is `.example` and not the `.test` the ticket names: a seeded
    account nobody can sign in as is not an account.

    Asserted here, at the boundary, so that a dependency bump which adds
    `example` to that list fails by name instead of as a 422 in an API test.
    """

    for account in ACCOUNTS:
        assert LoginRequest(email=account.email, password=SEED_PASSWORD)
        assert UserResponse(
            id=UUID(int=0),
            email=account.email,
            nickname=account.nickname,
            authority="USER",
            is_admin=False,
            is_active=True,
        )


# ---------------------------------------------------------------------------
# 3. Real event streams, the same state twice, and a name that is checked
# ---------------------------------------------------------------------------


async def _streams(session) -> dict[str, int]:
    rows = await session.execute(
        select(EventStoreORM.aggregate_type, func.count()).group_by(
            EventStoreORM.aggregate_type
        )
    )
    return {aggregate: count for aggregate, count in rows.all()}


def _rated_scenarios() -> list[tuple[SeedAccount, RatedRun]]:
    return [
        (account, scenario)
        for account in ACCOUNTS
        for scenario in account.scenarios
        if isinstance(scenario, RatedRun)
    ]


async def test_seeding_writes_an_event_stream_for_every_aggregate(session_factory):
    """The whole argument for going through the use cases, in one assertion: a
    directly-written row would leave these empty and everything else identical.

    The counts are lower bounds derived from the catalog rather than written
    down, so adding an account moves them without anybody editing a number.
    """

    async with session_factory() as session:
        seeded = await seed(session)
        streams = await _streams(session)

    assert len(seeded) == len(ACCOUNTS)
    # Two events per account, as a player writes them: the registration and the
    # naming (``docs/adr/0171`` §2). One would be an account seeded around the
    # act the gate holds every real account at.
    assert streams.get("user", 0) == 2 * len(ACCOUNTS)
    assert streams.get("assessment", 0) >= sum(
        len(account.scenarios) for account in ACCOUNTS
    )
    assert streams.get("skill_rating", 0) == len(_rated_scenarios())


async def test_every_rated_account_ends_in_the_band_its_name_promises(session_factory):
    """The catalog's claims, met by the engine the API actually serves.

    This is the assertion that makes the addresses mean something: a developer
    signing in as `rating-barely-established` is promised a Level just inside
    Established, and nothing but this says the answers still produce one.
    """

    async with session_factory() as session:
        await seed(session)
        ratings = await _stored_ratings(session)

    for account, scenario in _rated_scenarios():
        rating = ratings[(account.slug, scenario.sport)]
        assert (
            scenario.claim.complaint_about(
                band_name=rating.band_name,
                level=rating.mu,
                band_lower=rating.band_lower,
                band_upper=rating.band_upper,
            )
            is None
        )


async def _stored_ratings(session):
    """Every seeded rating, keyed by the account slug and the sport."""

    users = build_user_repository(session)
    ratings = build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )

    found = {}
    for account in ACCOUNTS:
        user = await users.get_by_email(account.email)
        assert user is not None
        for rating in await ratings.find_all_for(player_id=user.id):
            found[(account.slug, rating.sport)] = rating
    return found


async def test_a_name_that_stops_matching_its_state_stops_the_seed(
    session_factory, monkeypatch
):
    """An engine retune that moves a seeded player is the case this exists for.

    Simulated from the other side — the claim is moved rather than the engine —
    because the two are the same disagreement and only one of them can be
    written in a test.
    """

    account, scenario = _rated_scenarios()[0]
    monkeypatch.setattr(
        "app.seeds.runner.ACCOUNTS",
        (
            replace(
                account,
                scenarios=(replace(scenario, claim=RatingClaim(band="Advanced")),),
            ),
        ),
    )

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="named for a state it no longer"):
            await seed(session)


async def test_the_claim_is_checked_on_a_run_that_creates_nothing(
    session_factory, monkeypatch
):
    """The account seeded a month ago is the one nobody would check otherwise.

    The first run is honest and writes the rating; the second finds everything
    already there and creates nothing — and still refuses, because the claim is
    checked against the *stored* rating rather than against the result of a
    completion this run happened to perform.
    """

    account, scenario = _rated_scenarios()[0]
    monkeypatch.setattr(
        "app.seeds.runner.ACCOUNTS", (replace(account, scenarios=(scenario,)),)
    )

    async with session_factory() as session:
        await seed(session)

        monkeypatch.setattr(
            "app.seeds.runner.ACCOUNTS",
            (
                replace(
                    account,
                    scenarios=(replace(scenario, claim=RatingClaim(band="Advanced")),),
                ),
            ),
        )
        with pytest.raises(SeedFailed, match="named for a state it no longer"):
            await seed(session)


async def test_a_questionnaire_that_never_stops_is_refused_rather_than_waited_out(
    session_factory, monkeypatch
):
    """A hang in a developer command reads as a broken database.

    Driven by lowering the bound rather than by breaking the engine, because the
    engine stopping is the thing being relied on and a test that broke it would
    be testing its own stub.
    """

    monkeypatch.setattr("app.seeds.runner.MAX_ANSWERS", 0)

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="still going"):
            await seed(session)


async def test_re_running_leaves_the_same_state(session_factory):
    """Not "does not crash": the same ids, and a second run that says it created
    nothing.

    The event counts are the load-bearing half. `assessment-abandoned` is why:
    every finder answers *what is open*, and an abandoned run is not — so a
    probe that only asked a finder would start a second run beside the first,
    with both seed runs reporting success and the account holding a state its
    name does not describe.
    """

    async with session_factory() as session:
        first = await seed(session)
        streams_after_first = await _streams(session)
        second = await seed(session)
        streams_after_second = await _streams(session)

    assert [entry.player_id for entry in first] == [entry.player_id for entry in second]
    assert [
        [scenario.assessment_id for scenario in entry.scenarios] for entry in first
    ] == [[scenario.assessment_id for scenario in entry.scenarios] for entry in second]
    assert all(entry.registered for entry in first)
    assert not any(entry.registered for entry in second)
    assert not any(scenario.created for entry in second for scenario in entry.scenarios)
    assert all(entry.already_present for entry in second)
    assert streams_after_first == streams_after_second, "a re-run appended events"


def _a_run(*accounts: SeededAccount) -> SeedReport:
    """One run's report, with no cohort in it.

    The cohort's own lines are asserted in `test_seed_cohort.py`, against a run
    that really wrote one — a hand-built cohort here would be this test agreeing
    with a shape it invented.
    """

    return SeedReport(accounts=accounts, members=(), now=build_clock().now())


def test_the_report_names_the_address_the_password_and_every_state():
    """What a developer reads. Built from the run rather than from the catalog,
    so it cannot describe an account the run did not touch."""

    account = next(entry for entry in ACCOUNTS if entry.slug == "rated-in-every-sport")
    lines = report(
        _a_run(
            SeededAccount(
                account=account,
                player_id=UUID(int=1),
                registered=True,
                scenarios=tuple(
                    SeededScenario(
                        scenario=scenario,
                        assessment_id=UUID(int=index + 2),
                        created=True,
                    )
                    for index, scenario in enumerate(account.scenarios)
                ),
            )
        )
    )
    text = "\n".join(lines)

    assert account.email in text
    assert SEED_PASSWORD in text
    assert account.description in text
    assert "created" in text
    assert str(UUID(int=1)) in text
    for index, scenario in enumerate(account.scenarios):
        assert scenario.sport.value in text
        assert str(UUID(int=index + 2)) in text


def test_the_report_says_which_state_each_scenario_is_in():
    """Three states that read identically without the word: an open run, an
    abandoned one, and a rating. All three are an address and an assessment id."""

    states = report(
        _a_run(
            SeededAccount(
                account=SeedAccount(slug="probe", description="probe"),
                player_id=UUID(int=1),
                registered=False,
                scenarios=(
                    SeededScenario(
                        scenario=OpenRun(sport=Sport.PADEL),
                        assessment_id=UUID(int=2),
                        created=False,
                    ),
                    SeededScenario(
                        scenario=AbandonedRun(sport=Sport.TENNIS),
                        assessment_id=UUID(int=3),
                        created=False,
                    ),
                    SeededScenario(
                        scenario=RatedRun(
                            sport=Sport.SQUASH,
                            answers=AnswerPolicy(claims=2, demonstrations=2),
                            claim=RatingClaim(band=BAND_ESTABLISHED),
                        ),
                        assessment_id=UUID(int=4),
                        created=False,
                    ),
                ),
            )
        )
    )
    text = "\n".join(states)

    assert "PADEL in progress" in text
    assert "TENNIS abandoned" in text
    assert f"SQUASH rated ({BAND_ESTABLISHED})" in text
    assert "already present" in text


# ---------------------------------------------------------------------------
# 4. The command runs
# ---------------------------------------------------------------------------


async def test_the_command_seeds_a_real_database_and_is_idempotent(tmp_path):
    """`python -m app.seeds`, twice, against a database on disk.

    The subprocess is the point. Everything above imports the runner and calls
    it; this is the entry point `make seed` invokes, with the schema created the
    way a migration would have left it and nothing of the test process shared
    with it.
    """

    database = tmp_path / "seed.db"
    url = f"sqlite+aiosqlite:///{database}"

    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    # Built from nothing, so the subprocess inherits none of `conftest.py`'s
    # environment and every value is spelled here.
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(ROOT),
        "APP_ENV": "local",
        "JWT_SECRET_KEY": "test-secret-do-not-use-in-prod",
        "WRITER_DB_URL": url,
        "DB_SSL_MODE": "disable",
        # The fake, whatever a developer's `.env` selects: on Stripe the seed
        # asks for onboarded accounts first (#712).
        "PAYMENTS_PROVIDER": "fake",
        # The suite's work factor. A first run registers sixty-three accounts,
        # which is twelve seconds of hashing at production's strength.
        "BCRYPT_ROUNDS": str(BCRYPT_MINIMUM_ROUNDS),
    }

    def run_command() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "app.seeds"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

    first = run_command()
    assert first.returncode == 0, first.stderr
    for account in ACCOUNTS:
        assert account.email in first.stdout
    assert "[created]" in first.stdout

    second = run_command()
    assert second.returncode == 0, second.stderr
    assert "[already present]" in second.stdout
    assert "[created]" not in second.stdout
