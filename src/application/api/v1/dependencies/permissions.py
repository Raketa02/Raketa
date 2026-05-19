from fastapi import Depends

from application.api.v1.dependencies.auth import get_current_user
from application.core.exceptions import ForbiddenError
from application.domain.user.entities import User


class RequireAuthority:
    """Active dependency — 403 when the user's authority does not match.

    Replaces the no-op `PermissionDependency([])` pattern from the reference."""

    def __init__(self, *authorities: str) -> None:
        if not authorities:
            raise ValueError("RequireAuthority needs at least one authority")
        self._allowed = {a.upper() for a in authorities}

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if (user.authority or "").upper() not in self._allowed:
            raise ForbiddenError(
                "insufficient privileges",
                details={"required_any_of": sorted(self._allowed)},
            )
        return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise ForbiddenError("admin role required")
    return user
