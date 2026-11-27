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
path — `rakieta://administrator/<club>/you` or `rakieta://question/<id>` open nothing — which is the
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
which answers to `rakieta://`.

**The app's bare address, `rakieta://`, is the fourth thing read** — because it is the button of the
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
spells the group's link back from it — `rakieta://join/<code>` while no domain is set,
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
stays down; and a group link lands on Play under Join — on the _Groups_ title while the `explore`
feature flag is off, which is every phone today, and on Play's remembered segment, which may be
Explore, only while it is on (#826).
**A backend contract gap, open**: the club's email to an existing account opens bare `rakieta://`, so
the app cannot tell whose invitation it is — **Kuba's phone opening Tomek's _existing-account_ email
cannot name Tomek's address**; only a new person's token link can. Naming it would need that email to
carry a link the app can read (a token, or the invitation's id with a read by it).
**Nothing here has been seen on a device**, and no universal or app link can be until a domain exists
(ADR-0187 _Harder_).

## A friend link, and the link an Android install carried (#756)

**A fourth page: `f/<code>`, a friend link** ([#756](https://github.com/Raketa02/Raketa/issues/756),
PRD [#743](https://github.com/Raketa02/Raketa/issues/743); the friends mechanics §4.2–§4.3). Tomek's
link, `<public site>/f/<code>`, opens the app by the scheme and, once a domain is set, by the domain:
`LINK_PAGES` gains `f`, so `app.config.ts`'s verified Android filter gains `/f/` with the rest (the
site's association file claims `/f/*` since #755). **Its code is checked like a group's** — eight
letters and digits, read lower case — by `friends`' own `parseFriendLinkCode`, the shape the server
mints; `friends` spells it rather than borrowing `groups`', since `groups` draws `friends`' pills.

**Held like a group link, whoever is on the phone** (`landingOf`): it is answered by opening it _as
the account_, so it waits through sign-in, sign-up, the naming and the profile steps, and is answered
once the account is in the player's app. **In an administrator area it moves as a group link does**
— a playing administrator is switched to Player, one who does not play waits — so the rule is one
function for both, `playersLinkMove` (formerly `groupLinkMove`): both are the player's.

**Answered by opening the code, then Home** (`FriendLink`, `friendLinkLanding`). `friends`' opening
answers where the opener stands with the owner: **`ASKED_YOU` lands on Home with Needs your answer
up** ([#817](https://github.com/Raketa02/Raketa/issues/817), ADR-0205 §1; until then Home's FRIEND
REQUESTS row at the top) — `shell`'s `openNeedsYourAnswer`, which lays Home's root down as `openTab`
does and raises the sheet, _tomek.k wants to be your friend_ in it — with Home and the bell read
again for the request and its notice. The opening resolves once that re-read has landed, so the
sheet opens on what Home says then. **A request swallowed by the owner's block answers the same, and
lands on Home as it is**, with no sheet: nothing waits, and the sheet is never shown empty
(ADR-0202's named cost; ADR-0205 §1's call). The walk is `friendLink.test.tsx`: from You, from a
cold start, through sign-up, from an administrator area and through an Android install, each landing
with the sheet up — and on Home already, and on a swallowed request.
**`NONE` (your own link) and `FRIEND` (a friend's, or your own request crossing theirs) move nobody.**
**A refusal is a toast, wherever the player is**: `friend_link_not_found` the public page's _Nothing
at that link_, `unblock_them_first` how to see the request (#748's call, and the sentence a call),
anything else its recovery sentence. Every outcome lets the link go: it is opened once and never
tried again. **It is answered now or not at all** — the opening sets `networkMode: 'always'`, so a
link opened offline fails and says so, rather than landing the player on Home on a reconnect they
never saw. **Opened again it makes no second request**, so it is retried as a read is: a lost race
(`concurrent_modification`) once, and a failure of the network's twice, before anything is said —
so a blip at the end of Zofia's onboarding does not cost her Tomek's request.

**The install referrer, read once on an Android phone's first launch.** The public site's Google
Play button carries its page's link through the install (#755); `expo-application`'s
`getInstallReferrerAsync` reads it, behind a new platform port (`installReferrer.ts`, the only
importer of `expo-application`, fenced and proven by `pnpm test:boundaries`; an iPhone answers
`null`, and is unchanged). `readTheInstallReferrerOnce` is a **launch step** — `bootstrapApp`'s
`readInstallReferrer`, supplied by the root layout after the session is restored and **never
awaited**: the splash does not wait on Google Play. It reads **once, ever** — a flag the phone keeps
for itself (`installReferrerRead`, under no account, kept at sign-out; a read that fails reads as
raised, because acting on a stale link every launch is the worse mistake) — and **a `join/` or `f/`
link in it is held as if it had been tapped**; it never replaces a link already held, which is the
newer. **The referrer is anybody's text**, as `rakieta://` is — any Play listing's address can carry any
referrer — so `readReferrerLink` reads the page and its value off any `http(s)` host (the laptop's
`http://localhost:3001` included) and **never a token**: no store button carries one, and Play keeps
a referrer for 90 days.

**Calls made here, open for the product owner**: the opening's refusal sentences (_Nothing at that
link_ reused from the public page; the blocked owner's _Unblock them in Blocked players_); `NONE`
and `FRIEND` moving nobody _silently_ — no toast saying _that's your own link_ or _you're already
friends_; a referrer link waiting behind any link already held; the flag reading as raised when the
store cannot be read; and the phone-wide flag standing outside ADR-0188 §2's table, **whose record
is owed from a root session**.

**Needs a new development build**: `expo-application` is now a direct dependency (it was already
linked through `expo-notifications`, so a recent build may well carry it — rebuild to be sure). **No
referrer can be seen until the app is installed from Google Play itself** — a sideloaded build has
none; the internal testing track is the first place it can be walked.
