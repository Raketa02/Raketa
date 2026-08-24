"""Two rules the ranked funnel keeps by *not* doing something.

Neither can be asserted by a green behavioural test, because both are satisfied
by an empty file and broken by the line somebody adds next week. So they are
walks over the feature's own source, each with a negative control proving the
detector can tell the offending shape from an innocent one.

* **Nothing is random.** ADR-0051 drops exploration: no seed, no draw, nothing
  recorded for replay. A shelf that shuffled would be a screen that reshuffles
  between two identical requests, which looks broken and is.
* **There is no player feed cache.** ADR-0068 deletes it by name — *"every ask
  pays the full funnel"* — because it was the only store on this screen keyed on
  the person asking, and therefore the only one that could hand her a stale
  answer to a direct question. The two that stay are keyed on a city and on a
  match, and the walk reads that off their signatures rather than their names.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW = ROOT / "app" / "modules" / "now"

#: Every way a Python file reaches a random number, by the name that would
#: appear in the source. Written out rather than matched by prefix, so a reader
#: can see what is refused and a fourteenth spelling has to be added on purpose.
DICE = frozenset(
    {
        "random",
        "shuffle",
        "sample",
        "choice",
        "choices",
        "randint",
        "randrange",
        "uniform",
        "getrandbits",
        "secrets",
        "SystemRandom",
    }
)


def _names(tree: ast.AST) -> set[str]:
    """Every identifier the module imports or calls, by the name it wrote."""

    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.Name):
            found.add(node.id)
    return found


def test_nothing_in_now_draws_a_random_number() -> None:
    """Exploration is dropped, and discovery is shelves 4 and 5.

    The prototype's list builder recorded its dice for replay. There is nothing
    to record, because nothing is drawn: the order is a total function of the
    candidates, so two identical requests answer identically and *"why is this
    card third?"* has one answer rather than a seed.
    """

    offenders: list[str] = []
    for path in sorted(NOW.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in sorted(_names(tree) & DICE):
            offenders.append(f"{path.relative_to(ROOT)}: {name}")

    assert offenders == []


def test_the_dice_walk_can_see_one() -> None:
    """The negative control, driven both ways."""

    caught = ast.parse(
        "import random\n\ndef pick(cards):\n    return random.choice(cards)\n"
    )
    missed = ast.parse("def pick(cards):\n    return cards[0]\n")

    assert _names(caught) & DICE
    assert not (_names(missed) & DICE)


def _stores() -> dict[str, set[str]]:
    """Every port in Now that **puts something in and takes it back out**.

    A store is what a cache is, and it is read off the return annotations rather
    than off the names — which is what stops a `PlayerFeedCache` from being
    missed for spelling itself differently.

    **Two halves, not one.** A port that writes and never answers cannot serve
    anybody a stale anything: it is a command. That distinction was free while
    every write in Now returned a value, and stopped being free when ADR-0087's
    `Standby.leave` arrived returning nothing — a delete keyed on a player,
    which the one-sided test read as a player-keyed cache. The property this
    file is about is *can this hand one player's answer to another*, and a port
    with no read cannot hand anything to anybody.
    """

    from typing import get_type_hints

    from app.modules.now.domain import ports

    found: dict[str, set[str]] = {}
    for name in dir(ports):
        port = getattr(ports, name)
        if not isinstance(port, type) or not name[0].isupper():
            continue
        keys: set[str] = set()
        writes = False
        reads = False
        for method in dir(port):
            attribute = getattr(port, method, None)
            if method.startswith("_") or not callable(attribute):
                continue
            try:
                hints = get_type_hints(attribute)
            except (TypeError, NameError):
                continue
            if "return" not in hints:
                continue
            if hints["return"] is type(None):
                writes = True
                keys |= {key for key in hints if key != "return"}
            else:
                reads = True
        if writes and reads:
            found[name] = keys
    return found


#: The stores whose key **is** a person, named rather than skipped. One, and it
#: is the push channel's (ADR-0062, `Raketa02/Raketa#84`): `PushLines` holds the
#: line a player's own lock screen shows, which is the only record of that fact
#: anywhere. There is nothing to recompute it from, so there is no answer a
#: stale row could disagree with — which is the whole of what ADR-0068's deleted
#: player-feed cache was, and the reason the key was ever a proxy for it.
#:
#: `PushDevices` is **not** here and does not need to be: it is written by a
#: device and filed under `(player, token)`, so the player names which row
#: exactly as she does in the offers table.
#:
#: A second name here is a decision somebody makes in a diff, and it should be
#: made against that sentence rather than against the key.
PLAYER_KEYED: frozenset[str] = frozenset({"PushLines"})


def test_the_six_stores_in_now_are_two_caches_and_four_records() -> None:
    """ADR-0068 deletes the **player feed** cache by name and keeps two others.

    *"Every ask pays the full funnel"*: the deleted one is the only place on this
    screen that could serve a stale answer to a direct question, because it was
    the only one keyed on the person asking. A seventh name appearing here is
    that one returning, whatever it is called.

    **The set grew by four and the guard did not weaken**, which is the thing to
    read. `Offers` and `CascadeWaves` are the invitation cascade's own tables
    (ADR-0061), `PushLines` and `PushDevices` are the push channel's, and all
    four are stores by this walk's definition — they put something in and take
    it back out — but none is a *cache*: what is in them is the only copy there
    is, so there is nothing they could be stale against. The list is here so
    that growth is a decision somebody makes in a diff.
    """

    assert set(_stores()) == {
        "ArrivalSets",
        "CascadeWaves",
        "Offers",
        "PushDevices",
        "PushLines",
        "ScoringContexts",
    }


def test_a_write_only_port_is_not_read_as_a_store() -> None:
    """The negative control for the two halves the walk now requires.

    Without it, `_stores` narrowing is a change nothing measures: a later
    session could put the one-sided test back and every case above would stay
    green, because there is no cache in this tree to catch. `Standby` is the
    live example — it deletes a row keyed on a player and answers nothing — and
    a port shaped like it must be absent from the walk *and* present in the
    module, or the walk is passing by having stopped looking.
    """

    from app.modules.now.domain import ports

    assert hasattr(ports, "Standby")
    assert "Standby" not in _stores()


def test_no_store_is_keyed_on_a_player_but_the_one_that_is_a_person() -> None:
    """Which is the property that makes them safe rather than their names.

    The new-arrivals set is filed under `city : sport : kind`, the scoring
    context under `matchId : recordVersion`, an offer under `vacancy : player`
    and a dispatch under `vacancy : wave`. None of them takes a **player** as
    the key it is *written* by, so none can hold one player's answer and hand it
    to another.

    The offers table is the interesting one: a player is half its primary key,
    and it is still not player-keyed by this walk's meaning — the row is filed
    under a hole and the player names which row, so there is no answer to *what
    does this player see* stored anywhere that a second player could be given.

    **One store is keyed on a person and is named above**, because the rule
    this walk enforces was always a rule about **caches** and the key was the
    proxy for it. The line a player's lock screen holds is not an answer
    computed from something else and kept — it is the only record of that fact —
    so a *stale* one is not a thing that can exist. Its real guarantee is
    behavioural and is asserted where it can fail
    (`tests/unit/test_push_stores.py`): one player's debt is never another's,
    and a token belongs to one player at a time.
    """

    stores = _stores()
    # An exemption naming a port nobody wrote is decoration that would let the
    # next player-keyed cache through under an inherited name.
    assert PLAYER_KEYED <= set(stores)
    for name, keys in stores.items():
        if name in PLAYER_KEYED:
            continue
        assert not any("player" in key.lower() for key in keys), (name, keys)


def test_the_player_keyed_store_is_really_keyed_on_a_player() -> None:
    """The other half of the exemption: it must still be describing the truth.

    If this stopped taking a player as the key it is written by, the exemption
    would be covering nothing and would sit here inviting a second name.
    Asserted from the walk's own reading rather than from the source, so it is
    the same reading the rule above is made with.
    """

    stores = _stores()
    for name in PLAYER_KEYED:
        assert any("player" in key.lower() for key in stores[name]), name


def test_the_walk_reaches_the_tree_it_is_claiming_about() -> None:
    # A glob matching nothing passes silently; the count is asserted rather than
    # trusted.
    assert len(list(NOW.rglob("*.py"))) >= 20
