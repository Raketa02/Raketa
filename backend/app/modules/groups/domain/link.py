"""The Group link: the public site's address, ``/join/``, and the group's code.

``docs/adr/0183`` §4. **The address is configuration and the shape is not**:
which domain the public site answers on is a setting read under the four
environment names (``docs/adr/0187`` §7), so it is handed in here by whoever
holds the settings, and this module only says how a link is built from it.
"""

from __future__ import annotations

from app.modules.groups.domain.value_objects import GroupCode


def group_link(public_site: str, code: GroupCode) -> str:
    """``<public site>/join/<code>`` — one slash between the two however the
    address was written."""

    return f"{public_site.rstrip('/')}/join/{code.value}"
