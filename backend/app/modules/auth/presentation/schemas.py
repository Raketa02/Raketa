from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.modules.auth.application.one_time_credentials import ClaimTicket
from app.modules.auth.application.token_rotation import TokenPair


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    @classmethod
    def from_pair(cls, pair: TokenPair) -> "TokenResponse":
        return cls(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            token_type=pair.token_type,
            expires_in=pair.expires_in,
        )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


# --- Forgot password? (docs/adr/0184 §5) ---------------------------------------


class ForgotPasswordRequest(BaseModel):
    """*Forgot password?*: the address to send a link and a code to."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class ClaimCodeRequest(BaseModel):
    """The address and the 8-character code from the email. The code is read
    forgivingly — case, spaces and dashes are ignored — and its length is not
    checked here: a code of the wrong length is simply not the right code, and
    is told ``code_incorrect`` as every other one is. The bound is a cap on
    what a request may carry, not a rule about codes."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    code: str = Field(..., min_length=1, max_length=64)


class ClaimTicketResponse(BaseModel):
    """A correct code, exchanged for a ticket the new password is set with."""

    ticket: str = Field(
        ...,
        description=(
            "Present it as `ticket` when setting the new password. Good for "
            "`expires_in` seconds, and never past the code's own hour; claiming "
            "the code again replaces it."
        ),
    )
    expires_in: int

    @classmethod
    def from_ticket(cls, ticket: ClaimTicket) -> "ClaimTicketResponse":
        return cls(ticket=ticket.ticket, expires_in=ticket.expires_in)


class NewPasswordRequest(BaseModel):
    """The new password, and **exactly one** of what opens the way to it: the
    `token` from the email's link, or the `ticket` a claimed code returned.

    The password carries no bound here, deliberately: the rule every account
    shares — 8 to 128 characters with a letter and a digit — is refused as
    `password_too_weak` naming the field, not as a validation error naming none.
    Sending both or neither of `token` and `ticket` is a malformed request rather
    than a person's mistake, and is the one refusal here that is a `422`.
    """

    model_config = ConfigDict(extra="forbid")

    token: Optional[str] = Field(default=None, min_length=1, max_length=256)
    ticket: Optional[str] = Field(default=None, min_length=1, max_length=256)
    password: str

    @model_validator(mode="after")
    def _exactly_one_way_in(self) -> "NewPasswordRequest":
        if (self.token is None) == (self.ticket is None):
            raise ValueError("send exactly one of token and ticket")
        return self
