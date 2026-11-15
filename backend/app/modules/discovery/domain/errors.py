"""What the Discovery context refuses (#793, #794, #795)."""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError


class NotANewInRaketaPage(BadRequestError):
    """A See all page asked after a cursor this server never wrote. A client's
    own bug, said so."""

    code = "not_a_new_in_raketa_page"

    def __init__(self) -> None:
        super().__init__("Not a page of New in Raketa: an unreadable cursor.")


class NotASameLevelPage(BadRequestError):
    """A See all page of *Same competitive level* asked after a cursor this
    server never wrote (#794)."""

    code = "not_a_same_level_page"

    def __init__(self) -> None:
        super().__init__(
            "Not a page of Same competitive level players: an unreadable cursor."
        )


class NotASameVibePage(BadRequestError):
    """A See all page of *Same vibe players* asked after a cursor this server
    never wrote (#795)."""

    code = "not_a_same_vibe_page"

    def __init__(self) -> None:
        super().__init__("Not a page of Same vibe players: an unreadable cursor.")
