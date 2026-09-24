"""The split groups add up to the suite — the check's own arithmetic.

``make split-partition`` collects the suite and each group through the target CI
runs (``make test-group``), and hands the ids here. What is asserted below is the
part that decides: a test in no group, a test in two, and a test a group ran that
the suite never collected are each named, and a true partition names nothing.
"""

import json

from scripts.split_partition import a_stale_copy_of, nodeids_in, partition_of


def test_groups_that_add_up_to_the_suite_name_nothing():
    partition = partition_of(
        collected=["tests/a.py::one", "tests/a.py::two", "tests/b.py::three"],
        groups={1: ["tests/a.py::one", "tests/b.py::three"], 2: ["tests/a.py::two"]},
    )

    assert partition.adds_up
    assert partition.missing == ()
    assert partition.duplicated == ()
    assert partition.foreign == ()


def test_a_test_no_group_runs_is_named_missing():
    partition = partition_of(
        collected=["tests/a.py::one", "tests/a.py::two", "tests/b.py::three"],
        groups={1: ["tests/a.py::one"], 2: ["tests/b.py::three"]},
    )

    assert not partition.adds_up
    assert partition.missing == ("tests/a.py::two",)


def test_a_test_two_groups_run_is_named_duplicated():
    partition = partition_of(
        collected=["tests/a.py::one", "tests/b.py::three"],
        groups={1: ["tests/a.py::one", "tests/b.py::three"], 2: ["tests/b.py::three"]},
    )

    assert not partition.adds_up
    assert partition.duplicated == ("tests/b.py::three",)
    assert partition.missing == ()


def test_a_test_a_group_ran_and_the_suite_never_collected_is_named_foreign():
    """Only a collection that differs between runs produces one — which is itself
    a reason the groups cannot be trusted to add up."""

    partition = partition_of(
        collected=["tests/a.py::one"],
        groups={1: ["tests/a.py::one"], 2: ["tests/a.py::renamed"]},
    )

    assert not partition.adds_up
    assert partition.foreign == ("tests/a.py::renamed",)


def test_the_ids_are_read_off_a_collection_and_nothing_else_is():
    """The shape ``pytest --collect-only -q`` prints under pytest-split: its
    banner, one id per line — a parametrized one with spaces in it — then the
    summary."""

    output = (
        "\n"
        "[pytest-split] Splitting tests with algorithm: least_duration\n"
        "[pytest-split] Running group 1/2 (estimated duration: 15.00s)\n"
        "\n"
        "tests/unit/test_user_domain.py::test_email_rejects_garbage\n"
        "tests/api/test_deck.py::test_absent_from_the_deal[a game still ahead]\n"
        "\n"
        "2/27 tests collected (25 deselected) in 0.02s\n"
    )

    assert nodeids_in(output) == [
        "tests/unit/test_user_domain.py::test_email_rejects_garbage",
        "tests/api/test_deck.py::test_absent_from_the_deal[a game still ahead]",
    ]


def test_the_stale_copy_forgets_some_tests_and_remembers_one_that_is_gone(tmp_path):
    """What the stale pass rests on: tests written since the last refresh, which
    the file has never heard of, and a test deleted since, which it still has."""

    recorded = {f"tests/a.py::test_{n}": float(n) for n in range(6)}
    committed = tmp_path / ".test_durations"
    committed.write_text(json.dumps(recorded))

    stale = json.loads(a_stale_copy_of(committed, into=tmp_path).read_text())

    forgotten = recorded.keys() - stale.keys()
    remembered = recorded.keys() & stale.keys()
    gone = stale.keys() - recorded.keys()
    assert forgotten and remembered
    assert all(stale[nodeid] == recorded[nodeid] for nodeid in remembered)
    assert len(gone) == 1
