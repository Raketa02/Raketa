"""The container limit trigger 4 is read against.

``scale-posture.md`` §4 shipped both triggers instrumented. Trigger 1's two
instruments — the scoring histogram and the event-loop lag probe — went with the
searches that scored (#579); what is left is the one reading of the machine
trigger 4 needs, recomputed at every index load against the arithmetic in
``domain/scale_triggers.py``. The log record itself is written in
``app/bootstrap/jobs.py``.
"""

from __future__ import annotations

from pathlib import Path

#: cgroup v2, then v1. Read in that order because a v2 host also exposes the v1
#: tree under some configurations, and the unified hierarchy is the answer there.
CGROUP_V2_MEMORY_MAX = "sys/fs/cgroup/memory.max"
CGROUP_V1_MEMORY_LIMIT = "sys/fs/cgroup/memory/memory.limit_in_bytes"

#: cgroup v1 spells *unlimited* as a number rather than as a word — a page-aligned
#: near-2⁶³ — so anything above this is read as no limit at all rather than as a
#: container with nine exabytes in it.
UNLIMITED_ABOVE = 1 << 62


def container_memory_limit_bytes(root: Path = Path("/")) -> int | None:
    """This container's memory limit, or ``None`` where there is not one to read.

    **Unknown is not unlimited and not zero.** A laptop and a cgroup-less host
    have no limit to be half of, so trigger 4 cannot fire there and the record
    says the limit is unknown — where reporting a comfortable fraction of a
    made-up limit would be the invented measurement this map refuses everywhere
    else.

    ``root`` is a parameter so a test can drive both hierarchies and the absent
    case without a container, which is the only way this is exercised at all
    before there is a deployment.
    """

    for relative in (CGROUP_V2_MEMORY_MAX, CGROUP_V1_MEMORY_LIMIT):
        try:
            raw = (root / relative).read_text().strip()
        except OSError:
            continue
        if raw == "max":
            return None
        try:
            limit = int(raw)
        except ValueError:
            continue
        if limit <= 0 or limit > UNLIMITED_ABOVE:
            return None
        return limit
    return None
