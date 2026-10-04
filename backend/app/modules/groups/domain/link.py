"""The Group link: the public site's address, ``/join/``, and the group's code.

``docs/adr/0183`` §4. **The address is configuration and the shape is not**:
which domain the public site answers on is a setting read under the four
environment names (``docs/adr/0187`` §7), so it is handed in here by whoever
holds the settings, and this module only says how a link is built from it — and
how one is read back out of whatever a player pasted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, final

from app.modules.groups.domain.value_objects import GroupCode

#: ``/join/`` and whatever run of letters and digits follows it. The run is
#: taken whole, so a code with a ninth character is not quietly cut to eight;
#: and it stops at anything else, so the full stop ending a WhatsApp sentence or
#: a ``?utm_source=…`` is not part of it. ``join`` in any case, because a link
#: shouted in capitals is still that link.
_LINK_IN_TEXT: Final = re.compile(r"/join/([0-9A-Za-z]*)", re.IGNORECASE)


def group_link(public_site: str, code: GroupCode) -> str:
    """``<public site>/join/<code>`` — one slash between the two however the
    address was written."""

    return f"{public_site.rstrip('/')}/join/{code.value}"


@final
@dataclass(frozen=True, slots=True)
class PastedLink:
    """Text that holds a group link.

    ``code`` is the code it carries, or ``None`` when what follows ``/join/``
    could be **no group's** code — too short, too long, or with a look-alike in
    it. Either way it is a link, and a link that finds nothing is *nothing at
    that link*, never *no match* (#500 story 37).
    """

    code: GroupCode | None


def link_in(text: str) -> PastedLink | None:
    """The first group link in ``text``, or ``None`` when there is none.

    **Any text containing ``/join/<code>`` is recognised** (``docs/adr/0183``
    §4): a WhatsApp message with words around the link, a link with its scheme
    or without it, and a link printed under one environment's domain and pasted
    into another's. The domain is never read — it is the setting's business, and
    the code is the group's identity.

    Whether what follows ``/join/`` is a code is ``GroupCode``'s to say.
    """

    found = _LINK_IN_TEXT.search(text)
    if found is None:
        return None
    return PastedLink(code=GroupCode.read(found.group(1)))
