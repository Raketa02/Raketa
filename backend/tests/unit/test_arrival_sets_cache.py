"""The new-arrivals cache: fifteen minutes, and nothing to invalidate it.

The store's whole design is what it *cannot* do, and no green assertion carries
an absence on its own — so the surface is walked as well as exercised. A
``forget`` added next week would be a second thing to keep in step with the
truth, which is the reason ADR-0068 left it out.
"""

import inspect
from uuid import uuid4

from app.kernel import Sport

from app.modules.now.domain.arrivals import ARRIVAL_SET_TTL, ArrivalKey, ArrivalKind
from app.modules.now.domain.ports import ArrivalSets
from app.modules.now.infrastructure.arrival_sets import InMemoryArrivalSets
from tests.unit.arrival_doubles import StoppedClock

PLAYERS = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.PLAYERS)
CLUBS = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.CLUBS)


def _store(clock: StoppedClock) -> InMemoryArrivalSets:
    return InMemoryArrivalSets(clock=clock)


async def test_a_set_that_was_never_stored_is_nothing() -> None:
    assert await _store(StoppedClock()).get(PLAYERS) is None


async def test_a_stored_set_comes_back() -> None:
    store = _store(StoppedClock())
    ids = (uuid4(), uuid4())
    await store.put(PLAYERS, ids)

    assert await store.get(PLAYERS) == ids


async def test_an_empty_set_comes_back_as_an_empty_set_and_not_as_a_miss() -> None:
    # The distinction the composer depends on: *nobody arrived* is an answer
    # worth fifteen minutes, and a store that could not tell it from *never
    # asked* would pay the full query on every request in a quiet city.
    store = _store(StoppedClock())
    await store.put(CLUBS, ())

    assert await store.get(CLUBS) == ()


async def test_a_set_is_still_good_one_second_before_fifteen_minutes() -> None:
    clock = StoppedClock()
    store = _store(clock)
    ids = (uuid4(),)
    await store.put(PLAYERS, ids)

    clock.advance(minutes=ARRIVAL_SET_TTL, seconds=-1)
    assert await store.get(PLAYERS) == ids


async def test_a_set_is_gone_at_fifteen_minutes() -> None:
    clock = StoppedClock()
    store = _store(clock)
    await store.put(PLAYERS, (uuid4(),))

    clock.advance(minutes=ARRIVAL_SET_TTL)
    assert await store.get(PLAYERS) is None


async def test_an_expired_set_is_dropped_rather_than_kept_and_hidden() -> None:
    clock = StoppedClock()
    store = _store(clock)
    await store.put(PLAYERS, (uuid4(),))
    clock.advance(minutes=ARRIVAL_SET_TTL)
    await store.get(PLAYERS)

    assert PLAYERS.key not in store._held


async def test_the_ttl_runs_from_the_write_and_not_from_the_first_read() -> None:
    clock = StoppedClock()
    store = _store(clock)
    await store.put(PLAYERS, (uuid4(),))
    clock.advance(minutes=10)
    await store.get(PLAYERS)
    clock.advance(minutes=5)

    assert await store.get(PLAYERS) is None


async def test_a_second_write_replaces_the_first() -> None:
    store = _store(StoppedClock())
    await store.put(PLAYERS, (uuid4(),))
    fresh = (uuid4(), uuid4())
    await store.put(PLAYERS, fresh)

    assert await store.get(PLAYERS) == fresh


async def test_two_keys_do_not_reach_each_other() -> None:
    store = _store(StoppedClock())
    players = (uuid4(),)
    await store.put(PLAYERS, players)

    assert await store.get(CLUBS) is None
    assert await store.get(PLAYERS) == players


def test_the_cache_has_no_way_to_invalidate_an_entry() -> None:
    # The absence *is* the decision (ADR-0068): a method to clear an entry is a
    # method somebody eventually calls from a write, and then this is a second
    # thing to keep in step with the truth. The port is walked as well as the
    # adapter, because a port that grew one would be the invitation.
    for surface in (ArrivalSets, InMemoryArrivalSets):
        public = {
            name
            for name, _ in inspect.getmembers(surface, callable)
            if not name.startswith("_")
        }
        assert public == {"get", "put"}, surface


def test_the_value_type_cannot_hold_a_row() -> None:
    # *The set and not the row* is a type error rather than a rule. A nickname or
    # a club's name has to reach the next screen, and this is what stops one
    # being cached for fifteen minutes by somebody widening a signature.
    signature = inspect.signature(ArrivalSets.put)
    assert str(signature.parameters["ids"].annotation) == "tuple[UUID, ...]"
