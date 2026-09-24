"""The shards add up to the suite — a group's JUnit report, read back as test ids.

CI's backend groups each write a JUnit report of the tests they ran, and
``scripts.shards_add_up`` holds their union against the collected suite. The
arithmetic is ``partition_of``'s, tested beside it; what is asserted here is the
reading, **against a report a real pytest wrote**, because the report does not
carry a test's id. It carries a ``classname`` and a ``name`` mangled out of it,
and one test can own two ``<testcase>`` elements.
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scripts.shards_add_up import UnreadableReport, ids_in_report

SAMPLE = """
import pytest


def test_plain():
    pass


class TestAGroup:
    def test_in_a_class(self):
        pass


@pytest.mark.parametrize(
    "arg", [pytest.param(1, id="a game still ahead"), pytest.param(2, id="1.5/2")]
)
def test_parametrized(arg):
    pass


@pytest.mark.skip(reason="skipped, and still run by its group")
def test_skipped():
    pass


@pytest.fixture
def breaks_on_the_way_out():
    yield
    raise RuntimeError("teardown")


def test_fails_and_then_errors_in_teardown(breaks_on_the_way_out):
    assert False
"""

#: What ``pytest --collect-only -q`` prints for SAMPLE — the suite's own ids.
SUITE = [
    "tests/test_sample.py::test_plain",
    "tests/test_sample.py::TestAGroup::test_in_a_class",
    "tests/test_sample.py::test_parametrized[a game still ahead]",
    "tests/test_sample.py::test_parametrized[1.5/2]",
    "tests/test_sample.py::test_skipped",
    "tests/test_sample.py::test_fails_and_then_errors_in_teardown",
]


@pytest.fixture(scope="module")
def report(tmp_path_factory) -> Path:
    """SAMPLE run by a real pytest, which writes the report a CI group writes."""

    root = tmp_path_factory.mktemp("sample")
    (root / "pytest.ini").write_text("[pytest]\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_sample.py").write_text(SAMPLE)
    written = root / "report.xml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
            "-p",
            "no:cacheprovider",
            f"--junitxml={written}",
        ],
        cwd=root,
        capture_output=True,
    )
    return written


def test_a_report_reads_back_as_the_ids_of_the_tests_it_ran(report):
    assert sorted(ids_in_report(report, SUITE)) == sorted(SUITE)


def test_a_test_the_report_writes_twice_ran_once(report):
    """pytest writes a failure in the call and an error in the teardown as two
    elements with one address — a record of one run, not of two."""

    twice = "tests/test_sample.py::test_fails_and_then_errors_in_teardown"
    names = [case.get("name") for case in ET.parse(report).getroot().iter("testcase")]

    assert names.count(twice.rpartition("::")[2]) == 2
    assert ids_in_report(report, SUITE).count(twice) == 1


def test_a_test_the_suite_never_collected_comes_back_by_its_report_name(report):
    suite_without_one = [nodeid for nodeid in SUITE if not nodeid.endswith("_plain")]

    ran = ids_in_report(report, suite_without_one)

    assert "tests.test_sample.test_plain" in ran
    assert set(suite_without_one) <= set(ran)


def test_a_suite_two_of_whose_ids_read_alike_in_a_report_is_refused(report):
    """A report cannot say which of the two ran, so the check says it cannot
    tell rather than guessing."""

    alike = [
        "tests/test_sample.py::TestAGroup::test_in_a_class",
        "tests/test_sample/TestAGroup.py::test_in_a_class",
    ]

    with pytest.raises(UnreadableReport, match="TestAGroup"):
        ids_in_report(report, alike)


def test_a_report_that_is_not_xml_is_refused(tmp_path):
    broken = tmp_path / "group-1-of-2.xml"
    broken.write_text("<testsuites><testsuite>")

    with pytest.raises(UnreadableReport, match="group-1-of-2.xml"):
        ids_in_report(broken, SUITE)
