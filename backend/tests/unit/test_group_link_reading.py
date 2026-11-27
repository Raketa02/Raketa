"""Reading a group link out of whatever was pasted (``docs/adr/0183`` §4).

**Any text containing ``/join/<code>`` is a link**: a WhatsApp message with
words around it, a link with its scheme or without it, a link printed under one
environment's domain and pasted into another's. What follows ``/join/`` is the
code only if it is exactly a code — eight characters from the alphabet — so a
link that could name no group reads as a link that leads nowhere, never as text
to be searched for.
"""

from __future__ import annotations

import pytest

from app.modules.groups.domain.link import PastedLink, group_link, link_in
from app.modules.groups.domain.value_objects import GroupCode

CODE = GroupCode("ab3de7fg")


@pytest.mark.parametrize(
    "pasted",
    [
        "https://rakieta.app/join/ab3de7fg",
        "rakieta.app/join/ab3de7fg",
        "/join/ab3de7fg",
        "Join Ogrody 33 Club on Rakieta: https://rakieta.app/join/ab3de7fg — do it",
        "http://localhost:3001/join/ab3de7fg?utm_source=whatsapp",
        "https://rakieta.app/join/ab3de7fg.",
        "https://rakieta.app/join/ab3de7fg/",
        "HTTPS://RAKIETA.APP/JOIN/AB3DE7FG",
    ],
)
def test_a_link_anywhere_in_the_text_is_read_as_its_code(pasted):
    assert link_in(pasted) == PastedLink(code=CODE)


def test_the_link_a_group_is_given_reads_back_as_its_code():
    assert link_in(group_link("https://rakieta.app/", CODE)) == PastedLink(code=CODE)


@pytest.mark.parametrize(
    "pasted",
    [
        "rakieta.app/join/",
        "rakieta.app/join/ab3",
        "rakieta.app/join/ab3de7fgh",
        "rakieta.app/join/ab3de7f0",
        "rakieta.app/join/ab3de7fl",
        "rakieta.app/join/ab3de-7fg",
    ],
)
def test_a_link_whose_code_could_be_nobody_s_leads_nowhere(pasted):
    assert link_in(pasted) == PastedLink(code=None)


@pytest.mark.parametrize(
    "typed",
    ["ogrody", "join", "rakieta.app/g/ab3de7fg", "joinab3de7fg", "join/ab3de7fg"],
)
def test_text_without_slash_join_slash_is_not_a_link(typed):
    assert link_in(typed) is None


def test_the_first_link_in_the_text_is_the_one_read():
    assert link_in("/join/ab3de7fg and /join/zz22zz22") == PastedLink(code=CODE)
