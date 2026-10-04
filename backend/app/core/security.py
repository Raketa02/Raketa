"""Framework-level security primitives.

The HTTPBearer scheme is a FastAPI concept, not a domain port — concrete
hashing / token-issuing adapters live under each module's `infrastructure/`.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False, description="Bearer access token")

#: The bearer credentials a request presented, or ``None``. Declared once for
#: every surface that authenticates — the player app's and the club website's —
#: because what a bearer header *is* does not depend on whose token it carries;
#: which audience it must name is each surface's resolver's question.
BearerCredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]
