"""What the Discovery context refuses (#793)."""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError


class NotANewInRaketaPage(BadRequestError):
    """A See all page asked after a cursor this server never wrote. A client's
    own bug, said so."""

    code = "not_a_new_in_raketa_page"

    def __init__(self) -> None:
        super().__init__("Not a page of New in Raketa: an unreadable cursor.")
