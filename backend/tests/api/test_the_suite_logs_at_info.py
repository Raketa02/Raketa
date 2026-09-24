"""The suite logs at INFO, and that is a claim worth asserting.

`local` derives DEBUG, which is right for somebody running the app on a laptop
and wrong for a test run: the SQLite driver writes two DEBUG lines per
operation, and pytest keeps every record that reaches it for the report of the
test it happened in, whether or not anything ever reads it. That was about an
eighth of the suite's time. `conftest.py` sets `LOG_LEVEL` the way it sets its
other defaults — and were it to drop it, nothing would fail. The suite would
quietly go back to paying. A whole run with `LOG_LEVEL=DEBUG` set from outside
fails here too, which is this test reporting the same cost.

The level is the one thing changed. The logging plugin stays, because it is what
`caplog` is: `tests/unit/test_scheduled_jobs.py` and `test_live_channel.py`
assert on records through it, each at a level it sets for itself.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings


async def test_a_request_that_reaches_the_database_captures_no_debug_record(
    client, valid_signup_payload, caplog
):
    response = await client.post("/api/v1/users", json=valid_signup_payload)

    assert response.status_code == 201, response.text
    loggers_below_info = {r.name for r in caplog.records if r.levelno < logging.INFO}
    assert loggers_below_info == set()
    assert get_settings().LOG_LEVEL == "INFO"
