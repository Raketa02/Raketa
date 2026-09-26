# links — links into the app: a group link, an invitation's button, a reset's link

> The design record for `src/features/links/` — what the feature does and the reasons the shape is
> what it is, one paragraph per decision. **Append here** when a ticket changes what this feature
> does. Index: [`README.md`](README.md).

**Three links open the app, and nothing else does** ([#520](https://github.com/Raketa02/Raketa/issues/520),
PRD [#500](https://github.com/Raketa02/Raketa/issues/500) stories 46–48, 111–113, 117;
[ADR-0187](../../../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
§4, §7). They are the public site's pages that have an in-app twin: **`join/<code>`** — a **Group
link** out of WhatsApp — **`invite/<token>`**, an **Invitation**'s button, and **`reset/<token>`**, a
password reset's link. `src/app/+native-intent.ts` hands every address the operating system opens the
app with to `redirectSystemPath` (`components/redirectSystemPath`, over the `receiveLink` use-case)
before expo-router routes it, and **anything that is not exactly one of the three — or the app's bare
address, below — is ignored**: at a launch the app opens where it would
have with no link (`/`), and while it runs nothing moves. So no route is reachable from outside by its
path — `raketa://administrator/<club>/you` or `raketa://question/<id>` open nothing — which is the
stricter half of docs/architecture.md Part 2's _deep links are untrusted input_: the params of the
three are checked, and the rest are never routes at all.

**The reader is a list of what is accepted** (`schemas/incomingLinkUrl`). Where from: the app's own
scheme, the web domain once one is set (`https`, that host exactly — no port, no user, no other host),
or a path the router already holds. Which page: exactly two segments, the page and its value, so
`play/join/<code>` is no link. What value: a code by `groups`' shape (`GroupCodeSchema`, eight letters
and digits, read lower case) and a token by `auth`'s (URL-safe, 1–256), the shapes those features' own
routes read their params with. **The query and the fragment are dropped, never read**, and what comes
out is rebuilt from the checked parts, so no link carries an address, a flag or a host into the app —
**none can repoint the backend**: the API's address is configuration read once at launch, and nothing a
link holds reaches it. Expo Go's `exp://` is refused with the rest; the app runs as a development build,
which answers to `raketa://`.

**The app's bare address, `raketa://`, is the fourth thing read** — because it is the button of the
club's email to an account that already exists, which carries no token (ADR-0184 §2: _open Raketa,
signed in as you, and accept_). **Tapped while the app runs, it has the invitation sheet offer every
invitation set aside this launch again** — Tomek pressed _Not now_ earlier, and the button is him
asking. At a launch it is nothing: a launch from the home screen hands the router the same address,
and the sheet offers what is open on every launch anyway (`receiveLink`). So Tomek's own button, signed
out, is _sign in, then the sheet_ — the launch offer — and the token links below are a new person's,
and the club's reset of an administrator's.

**A link is held until a place that can answer it is reached** (`store/heldLink.store`, one at a time,
the latest winning). The rule is `domain/linkRules`' `landingOf`: **a group link is always held** —
Join a group is inside the player's app, and a person signed out, not yet onboarded or wearing their
administrator profile is not there — and **an invitation or a reset opens its own screen when nobody is
signed in**, _Set your password_ and _Set a new password_, and is held when somebody is. A cold start
does not know yet (the keychain is read after the link arrives), so it opens the screen, whose `(auth)`
guard hands a phone that turns out to be signed in to the gate. **In memory, and it dies with the
process**: a link tapped yesterday is not an instruction today, the reason the invitations set aside
live there too. **And it belongs to the session it arrived in** — or to the next one, when it arrived
with nobody signed in — **so a session's end lets it go** (`holdLink` watches the session machine for
signed in → signed out): an invitation's or a reset's token, or a group somebody tapped, is never
handed to the next person to sign in on the phone — the logout rule's _reset sensitive UI state_. A
one-time link's token is held for the moment it takes to answer it, and the screen it opens carries it
in its path anyway (#515's call); an account's own tokens are never here.

**The places are `IncomingLinks`, mounted over each home a signed-in account can be in** — the
player's app (`(app)/_layout`'s app branch, beside the invitation sheet) and an administrator area
(its route layout, beside the area: the area may not read this feature back). Nothing is mounted during
sign-in or onboarding, so nothing is answered there: **the group link Kasia opened before she had an
account waits through sign-up, the naming, the questionnaire and the social steps, and opens once the
data screen's _Start playing_ lands her in the app** (story 48; walked whole in `groupLink.test.tsx`).

**A group link opens Join a group with the link in its field and its group found under it**, over
Play › Groups so _back_ is the list (`shell`'s `openTab`, then the screen pushed) — story 46. The route
carries the code (`/play/join?code=`), checked by `groups`' `parseJoinRouteParams`, and the route file
spells the group's link back from it — `raketa://join/<code>` while no domain is set,
`https://<domain>/join/<code>` once one is (`shared/config/appLinks`' `appLinkTo`) — for the field, so
the search is the one a paste would have made. Which move a group link makes where the account is —
open Join, switch to Player, or wait — is `groupLinkMove`'s. **In an administrator area it switches to Player first** when the account
plays (the switcher's own move, `useSwitchProfile`), and the player's app answers it; **an account that
only runs a club's groups keeps it held**, and _Start playing_'s steps end on it.

**An invitation's link on a signed-in phone is read, then weighed against the account**
(`useInvitationLink`, then `invitationLinkOutcome`). **The account it was sent to** (addresses compared
trimmed and case-folded) **gets the Accept sheet** — the invitation sheet's, **that club's invitation**
taken back from what _Not now_ set aside this launch and no other club's (story 119), with `/users/me`
re-read for an invitation sent since (`administrator`'s `useOfferInvitationsAgain`, by the club name
`by-token` now carries); a **used** link opened by that account is how every new
person's walk ends, and says nothing. **Another address's open invitation gets a sheet naming the
address it is for, with _Sign out_** — Kuba's phone and Tomek's link. **A link that no longer works is
said, never signed out for**: its sentence, in `auth`'s words for it, as a toast. A read that fails says
why the same way. Which
outcomes let the link go is `letsTheLinkGo`'s. Signed out, the link opens _Set your password_ and
**stays held**: an address that is already an account is refused there with _sign in to accept_, and
the sign-in is answered with the sheet — _a signed-out person signs in first, then gets the sheet_.

**A reset link on a signed-in phone asks first** — _Set a new password?_, who is signed in, **Sign out**
or **Stay signed in**. Its link names no account (the player surface has no read of a reset token), so
the app cannot tell whether it is this account's, and setting a password through it begins a session as
whichever account it was sent to — somebody else's reset link would sign the phone into their account.
The invitation's sheet asks for the same reason, and there the address can be named. **This answers
#515's handover** (a reset link under the `(auth)` guard never reached a signed-in phone): the route
stays where it is, and a sheet stands in front of it. Signed out, the link opens the screen, which **lets
it go** (`useResetLinkOpened` in the route file) — otherwise the session its password begins would meet
the still-held link as a signed-in phone and be asked to sign out.

**_Sign out_ on either sheet leads to the link's own screen, signed out** — `auth`'s sign-out sequence
and its words (`SIGN_OUT`), then `router.replace` to `invite/<token>` or `reset/<token>`, awaited
through `mutateAsync` because the host is unmounted the moment the session ends and a `mutate`
callback would never be heard. The session's end lets the held link go; the screen needs only the token
in its path, and Tomek signing in there is offered the invitation by the launch's own sheet, while Kuba
signing back in is asked nothing. A sign-out that failed leaves the sheet up and says why, as the You
tab's does. **_Stay signed in_ lets the link go**, and so does the sheet's close, named _Not now_ so that
no two controls share a name.

**The web domain is a setting, and none is set** (`EXPO_PUBLIC_LINK_DOMAIN`, bare host, optional;
`shared/config/appLinks`). `app.config.ts` gives iOS an associated domain and Android one **verified**
intent filter for `/join/`, `/invite/` and `/reset/` over `https` only when it is set, and the running app
reads the same variable through the same function, so the binary and the app agree about which links are
the app's. While it is empty — every environment today — the links use the scheme alone, and the site's
_Open in Raketa_ (#526) is what opens the app.

**Calls made here, open for the product owner**: a reset link on a signed-in phone asks to sign out
rather than opening _Set a new password_ over the session; the app's bare address re-offers every
invitation set aside this launch; a spent invitation link opened signed in is a
toast; the two sheets' words (_This invitation is for …_, _Set a new password?_, _Stay signed in_, _Not
now_); a group link in the area switches a playing administrator to Player, and waits for one who does
not play; the field shows the scheme's spelling of the link while no domain is set, and the keyboard
stays down; and a group link lands on Play's remembered segment under Join, which may be Explore.
**A backend contract gap, open**: the club's email to an existing account opens bare `raketa://`, so
the app cannot tell whose invitation it is — **Kuba's phone opening Tomek's _existing-account_ email
cannot name Tomek's address**; only a new person's token link can. Naming it would need that email to
carry a link the app can read (a token, or the invitation's id with a read by it).
**Nothing here has been seen on a device**, and no universal or app link can be until a domain exists
(ADR-0187 _Harder_).
