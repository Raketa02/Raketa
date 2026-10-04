"""The one shape every Raketa email takes: a heading, a few lines, a button, and
— when the email opens something — its code. **A notice has no button**: an
email that only tells somebody what happened, and asks nothing of them, leads
nowhere (``docs/adr/0191`` §5).

**An email's words live here, in the backend** (``docs/adr/0186`` §4). The rule
that the API carries codes and never sentences exists for text a client renders,
and an email has no client: it goes from this process to a mailbox. So the
backend is the renderer, and every message is written twice, as **plain text and
as HTML**, from the same parts — the plain text is what a person whose mail
program shows no HTML reads, and it carries the link written out in full.

Everything interpolated into the HTML is escaped, including the link: a link
built from configuration and a token is still text, and a quote in either would
otherwise end the attribute.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from typing import Optional, TypeAlias, final

from app.application.ports.mail import OutgoingMessage
from app.kernel import invariant

#: Who signs every email. The brand is Raketa everywhere (``docs/adr/0187`` §8).
SIGNATURE = "Raketa"

#: The button's colour: the player app's ``coralInk``, because white text on its
#: ``coral`` fails contrast and white on this passes (5.89:1). Spelled here rather
#: than shared — an email is a client of nobody's design tokens.
_BUTTON_COLOUR = "#B8351C"


@final
@dataclass(frozen=True, slots=True)
class OnScreen:
    """Words the person has to find on a screen: a button's or a link's label.

    Inside a sentence a label is easy to read past — *tap Have an invitation
    code? under Sign in* is one run of words, and the label's own question mark
    reads as the sentence's. So it stands out: **bold** in the HTML, and in
    quotes in the plain text, which has no bold.
    """

    text: str


#: A line of words, some of which may be a label to find.
Phrase: TypeAlias = str | tuple[str | OnScreen, ...]


@final
@dataclass(frozen=True, slots=True)
class ButtonEmail:
    """The parts one message is rendered from."""

    kind: str
    to: str
    subject: str
    heading: str
    lines: Sequence[str]
    #: Where the email leads, and what its button says — both, or neither for
    #: a notice.
    button_label: Optional[str] = None
    button_url: Optional[str] = None
    #: The 8-character code, for an email that carries a credential, and the
    #: line that says what to do with it.
    code: Optional[str] = None
    code_line: Optional[Phrase] = None
    #: What a person who did not ask for this email should do.
    footer: Optional[str] = None

    def __post_init__(self) -> None:
        invariant(
            (self.button_label is None) == (self.button_url is None),
            "a button needs both its label and its address",
        )
        invariant(
            self.code is None or self.button_url is not None,
            "a code opens what the button opens, so it needs one",
        )


def render(email: ButtonEmail) -> OutgoingMessage:
    """The message, as plain text and HTML."""

    return OutgoingMessage(
        kind=email.kind,
        to=email.to,
        subject=email.subject,
        text=_text(email),
        html=_html(email),
    )


def _text(email: ButtonEmail) -> str:
    parts: list[str] = [email.heading, ""]
    for line in email.lines:
        parts.extend([line, ""])
    if email.button_url is not None:
        parts.extend([f"{email.button_label}:", email.button_url, ""])
    if email.code is not None:
        if email.code_line:
            parts.append(_plain(email.code_line))
        # On a line of its own, so it can be read and typed without its
        # neighbours, and found by a person scanning the email for it.
        parts.extend(["", email.code, ""])
    if email.footer:
        parts.extend([email.footer, ""])
    parts.append(f"— {SIGNATURE}")
    return "\n".join(parts) + "\n"


def _html(email: ButtonEmail) -> str:
    paragraphs = "".join(
        f'<p style="margin:0 0 16px">{escape(line)}</p>' for line in email.lines
    )
    button = (
        ""
        if email.button_url is None or email.button_label is None
        else (
            f'<p style="margin:24px 0">'
            f'<a href="{escape(email.button_url, quote=True)}" '
            f'style="display:inline-block;padding:12px 24px;border-radius:8px;'
            f"background:{_BUTTON_COLOUR};color:#ffffff;font-weight:600;"
            f'text-decoration:none">{escape(email.button_label)}</a></p>'
        )
    )
    code = ""
    if email.code is not None:
        code_line = (
            f'<p style="margin:0 0 8px">{_marked_up(email.code_line)}</p>'
            if email.code_line
            else ""
        )
        code = (
            f"{code_line}"
            f'<p style="margin:0 0 24px;font-family:monospace;font-size:24px;'
            f'letter-spacing:4px;font-weight:600">{escape(email.code)}</p>'
        )
    footer = (
        f'<p style="margin:0 0 16px;color:#6b6b6b">{escape(email.footer)}</p>'
        if email.footer
        else ""
    )
    return (
        "<!doctype html>"
        '<html><body style="margin:0;padding:24px;font-family:-apple-system,'
        "BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
        'color:#1a1a1a;line-height:1.5">'
        f'<h1 style="font-size:20px;margin:0 0 16px">{escape(email.heading)}</h1>'
        f"{paragraphs}{button}{code}{footer}"
        f'<p style="margin:0;color:#6b6b6b">— {escape(SIGNATURE)}</p>'
        "</body></html>"
    )


def _plain(phrase: Phrase) -> str:
    if isinstance(phrase, str):
        return phrase
    return "".join(
        f"“{part.text}”" if isinstance(part, OnScreen) else part for part in phrase
    )


def _marked_up(phrase: Phrase) -> str:
    if isinstance(phrase, str):
        return escape(phrase)
    return "".join(
        f"<strong>{escape(part.text)}</strong>"
        if isinstance(part, OnScreen)
        else escape(part)
        for part in phrase
    )
