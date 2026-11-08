"""What the Rankings context refuses (#770)."""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError


class NotAPage(BadRequestError):
    """A page asked for that names no page: a cursor this server never wrote,
    or a page asked for in two places at once — *after* and *before*, or
    either with *around me*. A client's own bug, said so."""

    code = "not_a_ranking_page"

    def __init__(self, why: str) -> None:
        super().__init__(f"Not a page of the ranking: {why}.")
