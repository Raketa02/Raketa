"""The container limit trigger 4 is read against, from a tree a test states.

Trigger 1's two instruments — the scoring meter and the loop-lag probe — went
with the searches that scored (#579). What is left reads the cgroup files, and
``root`` is a parameter so both hierarchies and the absent case are driven
without a container.
"""

from __future__ import annotations

from pathlib import Path


from app.modules.matchmaking.infrastructure.scale_instruments import (
    container_memory_limit_bytes,
)


# ---------------------------------------------------------------------------
# The container limit trigger 4 is read against


def test_the_v2_limit_is_read(tmp_path: Path) -> None:
    (tmp_path / "sys/fs/cgroup").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory.max").write_text("1073741824\n")
    assert container_memory_limit_bytes(tmp_path) == 1_073_741_824


def test_a_v2_container_with_no_limit_reads_unknown(tmp_path: Path) -> None:
    (tmp_path / "sys/fs/cgroup").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory.max").write_text("max\n")
    assert container_memory_limit_bytes(tmp_path) is None


def test_the_v1_limit_is_read_when_there_is_no_v2_tree(tmp_path: Path) -> None:
    (tmp_path / "sys/fs/cgroup/memory").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory/memory.limit_in_bytes").write_text(
        "536870912\n"
    )
    assert container_memory_limit_bytes(tmp_path) == 536_870_912


def test_v1s_numeric_spelling_of_unlimited_is_not_a_nine_exabyte_container(
    tmp_path: Path,
) -> None:
    """cgroup v1 spells *no limit* as a page-aligned near-2⁶³ rather than as a
    word, and a container with nine exabytes in it is not a thing."""

    (tmp_path / "sys/fs/cgroup/memory").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory/memory.limit_in_bytes").write_text(
        "9223372036854771712"
    )
    assert container_memory_limit_bytes(tmp_path) is None


def test_a_host_with_no_cgroup_at_all_reads_unknown(tmp_path: Path) -> None:
    """A laptop. **Unknown is not unlimited** — trigger 4 simply cannot fire."""

    assert container_memory_limit_bytes(tmp_path) is None
