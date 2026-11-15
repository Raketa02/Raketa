"""What the Rankings context refuses (#770, #797)."""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError


class NotAPage(BadRequestError):
    """A page asked for that names no page: a cursor this server never wrote,
    or a page asked for in two places at once — *after* and *before*, or
    either with *around me*. A client's own bug, said so."""

    code = "not_a_ranking_page"

    def __init__(self, why: str) -> None:
        super().__init__(f"Not a page of the ranking: {why}.")


class NotOneSport(BadRequestError):
    """Top 10 asked for in no sport, or in two at once: a sport asked for
    exactly and a preferred one together, or neither (#797). A client's own
    bug, said so."""

    code = "not_one_sport"

    def __init__(self) -> None:
        super().__init__(
            "Top 10 reads one sport: a sport asked for, or one preferred — never "
            "both, never neither."
        )
