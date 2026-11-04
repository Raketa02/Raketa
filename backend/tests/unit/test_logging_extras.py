"""A log line's ``extra`` may not name an attribute ``LogRecord`` already has.

``logging`` refuses one with ``KeyError("Attempt to overwrite 'name' in
LogRecord")`` — at the call, and only when the level is enabled. So an audit
handler that names one passes every test that logs below INFO and **fails its
delivery wherever INFO is on**, which is everywhere that runs, and the outbox
retries it. ``LogUserNamed`` did exactly that with ``name``.
"""

from __future__ import annotations

import ast
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.application.events import DeliveryContext
from app.modules.users.application.handlers import log_user_registered
from app.modules.users.application.handlers.log_user_registered import LogUserNamed
from app.modules.users.domain.events import UserNamed, UserNamedV1

APP = Path(__file__).resolve().parents[2] / "app"

#: What a record is born with, and the two keys ``Formatter`` writes onto it.
RESERVED = frozenset(
    logging.LogRecord("n", logging.INFO, "p", 0, "m", None, None).__dict__
) | {"message", "asctime"}

NOW = datetime(2026, 10, 7, 9, tzinfo=timezone.utc)


async def test_the_naming_is_logged_with_the_nickname_only(caplog):
    """The log line records the nickname and nothing else that names a person
    (``docs/adr/0199`` §1): no account holds a name to log."""

    caplog.set_level(logging.INFO, logger=log_user_registered.__name__)
    user_id = uuid4()

    await LogUserNamed()(
        UserNamed(user_id=user_id, nickname="ania.k", occurred_at=NOW),
        DeliveryContext(event_id=uuid4(), attempt=1, occurred_at=NOW),
    )

    [record] = [r for r in caplog.records if r.getMessage() == "user.named"]
    assert record.user_id == str(user_id)
    assert record.nickname == "ania.k"
    assert not hasattr(record, "user_name")


async def test_a_first_version_naming_is_logged_without_its_name(caplog):
    """A v1 row still in the outbox is delivered, and its name stays out of the
    log as it stays out of the fold."""

    caplog.set_level(logging.INFO, logger=log_user_registered.__name__)

    await LogUserNamed()(
        UserNamedV1(
            user_id=uuid4(), name="Ania Kowalska", nickname="ania.k", occurred_at=NOW
        ),
        DeliveryContext(event_id=uuid4(), attempt=1, occurred_at=NOW),
    )

    [record] = [r for r in caplog.records if r.getMessage() == "user.named"]
    assert record.nickname == "ania.k"
    assert not hasattr(record, "user_name")
    assert "Ania Kowalska" not in str(record.__dict__)


def test_no_log_line_in_the_app_names_a_record_attribute_in_its_extra():
    clashes = [
        f"{path.relative_to(APP.parent)}:{key.lineno} {key.value!r}"
        for path in sorted(APP.rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "extra" and isinstance(keyword.value, ast.Dict)
        for key in keyword.value.keys
        if isinstance(key, ast.Constant) and key.value in RESERVED
    ]

    assert clashes == []
