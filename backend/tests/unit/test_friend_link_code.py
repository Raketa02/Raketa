"""A Friend link's code is shaped like a group's (``docs/adr/0202`` §1; #748).

Friends imports no group (``.importlinter``'s
*friends-knows-none-of-its-readers*), so the alphabet and the length are spelled
twice — and held equal here.
"""

from __future__ import annotations

import pytest

from app.modules.friends.domain.link import (
    FRIEND_LINK_CODE_ALPHABET,
    FRIEND_LINK_CODE_LENGTH,
    FriendLinkCode,
    friend_link_url,
)
from app.modules.groups.domain.value_objects import (
    GROUP_CODE_ALPHABET,
    GROUP_CODE_LENGTH,
)


def test_a_friend_link_code_is_shaped_like_a_group_code():
    assert FRIEND_LINK_CODE_ALPHABET == GROUP_CODE_ALPHABET
    assert FRIEND_LINK_CODE_LENGTH == GROUP_CODE_LENGTH


def test_a_code_opened_in_capitals_is_the_same_code():
    assert FriendLinkCode.read("K7PM2QXA") == FriendLinkCode("k7pm2qxa")


@pytest.mark.parametrize(
    "typed",
    [
        "k7pm2qx",  # too short
        "k7pm2qxab",  # too long
        "k7pm2qx0",  # a zero, beside an o
        "k7pm2qx1",  # a one, beside an l
        "k7pm2qxl",  # an l, beside a one
        "k7pm-qxa",
        "",
    ],
)
def test_what_could_be_no_links_code_reads_as_none(typed):
    assert FriendLinkCode.read(typed) is None


def test_the_link_is_the_public_site_and_the_code():
    code = FriendLinkCode("k7pm2qxa")

    assert (
        friend_link_url("https://rakieta.app", code) == "https://rakieta.app/f/k7pm2qxa"
    )
    assert (
        friend_link_url("https://rakieta.app/", code)
        == "https://rakieta.app/f/k7pm2qxa"
    )
