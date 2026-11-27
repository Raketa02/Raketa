"""**What's new in Needs your answer** — the envelope's badge, kept on the
server the way the bell keeps its number (#815; ``docs/adr/0205`` §3).

**A visit is one watermark per player**, never a seen flag per item: closing
the sheet records the newest arrival it showed, and only what arrived after it
is new — on every phone at once. **It never moves back**: the same watermark
again records nothing, and neither does an older one, which a phone closing on
an older read after another phone closed on a newer one would send. The
watermark is the phone's, never the server's moment, so it is the watermark
that is compared; one past the server's clock was never served by any read,
and is refused.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import instant
from app.modules.proposals.domain.errors import WatermarkInTheFuture
from app.modules.proposals.domain.events import NeedsYourAnswerClosed
from app.modules.proposals.domain.needs_your_answer import (
    NeedsYourAnswerVisit,
    WhatIsNew,
    what_is_new,
)
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
#: What a read served: the newest arrival among what waited then.
SHOWN = AT - timedelta(minutes=5)


def a_visit() -> NeedsYourAnswerVisit:
    return NeedsYourAnswerVisit.from_history(new_uuid(), [])


# --------------------------------------------------------------------------- #
# The visit
# --------------------------------------------------------------------------- #


def test_a_sheet_never_closed_has_no_watermark():
    assert a_visit().watermark is None


def test_closing_the_sheet_records_the_watermark_it_showed_not_the_moment():
    visit = a_visit()

    closed = visit.close(watermark=SHOWN, at=AT)

    assert closed == NeedsYourAnswerClosed(
        player_id=visit.player_id, watermark=SHOWN, occurred_at=AT
    )
    assert visit.watermark == SHOWN
    assert visit.pull_events() == [closed]


def test_closing_it_again_on_the_same_read_records_nothing():
    visit = a_visit()
    visit.close(watermark=SHOWN, at=AT)
    visit.pull_events()

    assert visit.close(watermark=SHOWN, at=AT + timedelta(minutes=1)) is None
    assert visit.pull_events() == []


def test_an_older_watermark_never_moves_it_back():
    visit = a_visit()
    visit.close(watermark=SHOWN, at=AT)
    visit.pull_events()

    assert visit.close(watermark=SHOWN - timedelta(minutes=1), at=AT) is None
    assert visit.watermark == SHOWN
    assert visit.pull_events() == []


def test_a_later_watermark_moves_it_on():
    visit = a_visit()
    visit.close(watermark=SHOWN, at=AT)

    later = visit.close(watermark=AT, at=AT + timedelta(hours=2))

    assert later is not None
    assert (visit.watermark, visit.version) == (AT, 2)


def test_a_watermark_past_the_servers_clock_is_refused_and_records_nothing():
    visit = a_visit()

    with pytest.raises(WatermarkInTheFuture):
        visit.close(watermark=AT + timedelta(seconds=1), at=AT)

    assert visit.watermark is None
    assert visit.pull_events() == []


def test_the_stream_folds_back_into_the_last_watermark():
    visit = a_visit()
    visit.close(watermark=SHOWN, at=AT)
    visit.close(watermark=AT, at=AT + timedelta(hours=2))

    folded = NeedsYourAnswerVisit.from_history(visit.player_id, visit.pull_events())

    assert (folded.watermark, folded.version) == (AT, 2)


# --------------------------------------------------------------------------- #
# The count
# --------------------------------------------------------------------------- #


def test_before_any_visit_everything_waiting_is_new():
    arrivals = [SHOWN - timedelta(days=3), SHOWN]

    assert what_is_new(arrivals, seen_through=None) == WhatIsNew(
        count=2, watermark=SHOWN
    )


def test_only_what_arrived_past_the_watermark_is_new():
    arrivals = [SHOWN - timedelta(minutes=1), SHOWN, SHOWN + timedelta(seconds=1)]

    assert what_is_new(arrivals, seen_through=SHOWN) == WhatIsNew(
        count=1, watermark=SHOWN + timedelta(seconds=1)
    )


def test_the_reads_watermark_is_its_newest_arrival_whatever_was_seen():
    """What the phone sends back on closing: the newest the sheet showed,
    even when all of it was seen already."""

    arrivals = [SHOWN - timedelta(minutes=1), SHOWN]

    assert what_is_new(arrivals, seen_through=AT) == WhatIsNew(count=0, watermark=SHOWN)


def test_nothing_waiting_is_nothing_new_and_no_watermark():
    assert what_is_new([], seen_through=SHOWN) == WhatIsNew(count=0, watermark=None)
    assert what_is_new([], seen_through=None) == WhatIsNew(count=0, watermark=None)


# --------------------------------------------------------------------------- #
# To the millisecond, a phone's own precision
# --------------------------------------------------------------------------- #

#: An arrival recorded to the microsecond, as the store keeps it.
PRECISE = SHOWN + timedelta(microseconds=123_456)
#: The same instant as a phone's date holds it: to the millisecond.
TO_THE_MS = SHOWN + timedelta(microseconds=123_000)


def test_the_reads_watermark_is_served_to_the_millisecond():
    """A phone that turns it into its own date and back sends the same
    instant again."""

    assert what_is_new([PRECISE], seen_through=None).watermark == TO_THE_MS


def test_an_arrival_seen_to_the_millisecond_is_not_new():
    a_millisecond_before = TO_THE_MS - timedelta(milliseconds=1)

    assert what_is_new([PRECISE], seen_through=TO_THE_MS).count == 0
    assert what_is_new([PRECISE], seen_through=a_millisecond_before) == WhatIsNew(
        count=1, watermark=TO_THE_MS
    )


def test_a_visit_keeps_its_watermark_to_the_millisecond():
    visit = a_visit()

    visit.close(watermark=PRECISE, at=AT)

    assert visit.watermark == TO_THE_MS
    # The same instant to the millisecond is the same visit.
    assert visit.close(watermark=TO_THE_MS, at=AT) is None
