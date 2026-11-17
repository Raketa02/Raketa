"""The statement counter, ``statements`` (#812) — held to counting, since a
counter that heard nothing would pass every *at most one statement more* it is
asked."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import aliased

from app.modules.discovery.infrastructure.directory_model import (
    DirectoryPlayerORM,
    DirectoryTagORM,
)


async def test_it_counts_every_statement_inside_the_block_and_none_outside(
    session_factory, statements
):
    async with session_factory() as session:
        await session.execute(text("SELECT 1"))
        with statements.counting() as sent:
            await session.execute(text("SELECT 2"))
            await session.execute(select(DirectoryTagORM.tag))
        await session.execute(text("SELECT 3"))

    assert len(sent) == 2
    assert len(sent.naming("discovery_player_tags")) == 1
    # A table's name is a whole word: the tags are not the players.
    assert sent.naming("discovery_players") == []


async def test_a_table_read_under_an_alias_is_named_too(session_factory, statements):
    other = aliased(DirectoryPlayerORM)
    async with session_factory() as session:
        with statements.counting() as sent:
            await session.execute(
                select(DirectoryPlayerORM.player_id).join(
                    other, other.player_id == DirectoryPlayerORM.player_id
                )
            )

    [statement] = sent.naming("discovery_players")
    assert "discovery_players_1" in statement


async def test_a_statement_is_found_by_what_it_was_bound_to(
    session_factory, statements
):
    """One table, two contexts' rows: the text is the same, the binding is not
    (#814)."""

    async with session_factory() as session:
        with statements.counting() as sent:
            await session.execute(text("SELECT :kind"), {"kind": "skill_rating"})
            await session.execute(text("SELECT :kind"), {"kind": "player_profile"})
            await session.execute(text("SELECT 1"))

    assert len(sent) == 3
    assert len(sent.binding("skill_rating")) == 1
    assert sent.binding("nothing bound") == []


async def test_it_hears_every_statement_a_request_sends(
    client, statements, valid_signup_payload
):
    with statements.counting() as sent:
        signed_up = await client.post("/api/v1/users", json=valid_signup_payload)

    assert signed_up.status_code == 201, signed_up.text
    assert any(
        one.lstrip().upper().startswith("INSERT") for one in sent.naming("users")
    )
