# auth — sign up, sign in, session restore

> The design record for `src/features/auth/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**Sign-up asks whether the player is an adult, and it is an attestation.** The platform is
adults only, and that is a precondition of _holding an account_ rather than a rule about who
is shown to whom ([ADR-0124](../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
What the form collects is **one boolean — never a date of birth**, and it is **not age
verification**: there is no date picker anywhere in this app and this is not where the first
one arrives. The box is never pre-ticked, _Create account_ is never disabled by it, and the
refusal is a sentence under the box rather than a closed control
([ADR-0089](../../../docs/adr/0089-player-profile-context-event-sourced.md)). The same sentence
renders when the server refuses by `adult_attestation_required` — an older build or a
replayed request can carry a body this form would not have sent, and _try again_ would then
be the one thing that is not true.

**Sign-up asks for credentials only, and the naming is this feature's screen inside onboarding**
([#451](https://github.com/Raketa02/Raketa/issues/451),
[ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
The nickname left the sign-up form: choosing credentials and saying who you are are two different
moments, and a sign-up refused for a taken handle was a sign-up refused for a reason that had
nothing to do with the account. What replaces it is **the naming** — _How should people see
you?_ — a **Name** (free text, spaces allowed, never unique, 2–64 after the trim and the
collapse) and a **Nickname** (the handle under the rule the sign-up form used to state, unique),
submitted together as one act, `PUT /users/me/name`, repeatable. The screen lives in
`features/auth/` on the second part's own precedent — the values are the users context's and the
follow-up that edits them from the You tab will drive the same schema, mutation and sentences —
and the route file under `(onboarding)/` is what makes it onboarding's first screen. The
nickname's rule is written under its box before anything is typed, so a refusal never surprises;
a taken handle comes back by code with its field and lands under that box, exactly as the
sign-up conflicts always did. **The step cannot be skipped**: the device's back is claimed and
refused, and on success the mutation writes what the server recorded into the cached player and
_awaits_ a fresh read of `/me` before the screen hands the next destination to the entry gate —
`router.replace('/')`, as the data screen leaves the second part — because where a named player
belongs is the gate's rule and not this screen's. **The re-read is a `fetchQuery` on the one
query definition, not an invalidation**: nothing on the step observes the player, an unobserved
entry is garbage-collected after five minutes, and an invalidation of an entry that is not there
refetches nothing and resolves at once — the re-read would then be the gate's, which is correct
and not the promise. `fetchQuery` creates the entry where it has to and _throws where the read
failed_, so a naming the app could not confirm keeps the player on the step under the
could-not-reach banner rather than moving on; the act is repeatable, and the next _Continue_ is
the same request with a re-read that answers. `AuthenticatedUser` carries `name` and
`nickname`, both absent until the naming, and the **You tab draws the name, `@nickname` under it
and the email** — one of the two screens that draw a handle, the other being the record.

**The naming, from the You tab** ([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§7 — the follow-up ADR-0171 left open). **The refactor came first**: `useNamingForm` is the
form — what is typed, what the schema refuses before a round trip, the send through
`useNamePlayer`, the server's refusal with the field it names — and `NamingFields` draws the
two boxes, the handle's rule and each refusal under its box, with the banner above them; the
naming step is now that form under its own chrome (the eyebrow, the question, _Continue_, a
back that is refused), and its suite is unchanged. **`NameScreen`** is the same form under the
tab's chrome — _On your card · Name_, a way back, `avoidsKeyboard` — pre-filled from
`GET /users/me` with _Save_ where the step says _Continue_ and no sentence over the boxes: the
step's question does not need repeating on a screen that only edits the answer. A taken handle
is the server's `409 nickname_already_taken` on the press, drawn under the box in the app's own
sentence exactly as the step draws it, and never a lookup while typing (ADR-0159's
enumeration). The mutation writes what the server recorded and awaits the re-read before it
resolves, so the tab's header card and the **`NameRow`** — _Ada Lovelace · @ada_, the name and
the handle together or nothing, which makes the tab one of the two places the handle is drawn —
already say the new name on the way back. **`AccountPanel` is the button now.** The name, the
handle and the email it drew were the way to tell which player the gate let through while the
tab was a placeholder; the header card and the _Name_ row say the first two, and the email has
no row because it has no route (ADR-0179 §9) — a fact with no door under a list of facts with
doors reads as a broken row. _Sign out_ stays at the foot, `dark` and not `primary`, the only
way out of a session.

**A save on the Name screen stays, and turns _Save_ green** (2026-09-18, with the You tab's
other six _Save_s — design-system 6.1 as amended that day). The screen used to go back on its
own the moment the re-read landed, which was the one place on the tab where a save that landed
was never seen landing. Now the form is **a draft over the player**, the tab's shape for every
control behind a row: each box shows what was typed or the player's own answer while nothing
was, `changed` is the draft against what is held, and the draft is dropped when the mutation
resolves — after the re-read — so the boxes then hold **the server's re-read** and never what
was typed, and _Save_ is shut again as a green `settled` `Saved`, arriving on the button's own
fade. `onSaved` is optional: the naming step still passes `router.replace('/')`, the Name screen
passes nothing, and the way back is the header's. `nameFromYou.test.tsx` walks it. **Not seen
on a device**: the boxes re-drawn from the re-read under a green button.

**The signed-in player carries the tester mark, and nothing in the app branches on it**
([#479](https://github.com/Raketa02/Raketa/issues/479), [ADR-0180](../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md) §9). `/users/me` gained a
required `is_tester` (#478), and `AuthenticatedUser.isTester` carries it where `is_admin` is still
dropped — for the opposite reason: it grants nothing. Its one reader is flag evaluation, which
sends it as the `isTester` attribute so the flags repo's `testers` segment can reach a player
without the public datafile ever naming one. A screen that drew differently for a tester would be
the second, unreviewed flag system the ADR exists to prevent.

**_Forgot password?_ is four screens and a toast, made of the sign-in screen's pieces**
([#515](https://github.com/Raketa02/Raketa/issues/515),
[ADR-0184](../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
§5). It sits under the Sign in button on the one sign-in screen players and administrators share,
and walks: the email (`/forgot-password`, opened with whatever the sign-in box held), a neutral
confirmation (`/forgot-password/sent`), the email and the code (`/forgot-password/code`), and
_Set a new password_ — by a claimed code at `/forgot-password/new-password`, or by the email's
link at `/reset/<token>`, the path the email's button names and the one #520 opens from an
incoming link. **Nothing is drawn twice**: the sign-in screen was taken apart into `AuthFrame` (the
paper, the keyboard's avoidance, the scroll, _RAKETA_ over the title, and an optional `lead`),
`EmailField` (the five props that make a box an email box), `AuthLink` (the 44pt text link, by
`href` or by `onPress`) and `PasswordPairFields` (sign-up's two revealable boxes and the rule), and
sign-in, sign-up and the four new screens are each those pieces asking one thing. The route paths
are `RESET_ROUTES` (with `askForResetHref` for every way back to the email form), the recovery's
sentences are `resetPresentation`'s, and the words sign-in and sign-up still wrote inline moved to
`authPresentation` on the way past — a label a piece draws on six screens is copy with six readers.
The text link's press is 6.6's `.7`; the two screens it came from drew `.6`, which that table does
not have.

**The confirmation says one thing to everybody.** The server answers `202` for an address with an
account, without one, and past its silent three-an-hour throttle, so the screen after _Send_ is the
same screen in every case: _if_ that email has an account, a link and a code went to it, and both
work for an hour, once. The address is said back, because a typo is the likeliest reason nothing
arrives and saying it tells nobody anything the person did not type. The only failure the email
form can show is one about reaching the server.

**The code is read the server's way, and its length is checked here where the server does not.**
Spaces and dashes come out and it is upper-cased before it is sent, so `k7m4-qx2p` is the code. A
code of the wrong length can only be a wrong one, and five wrong codes lock the email — so the form
refuses it before it spends an attempt. A wrong code lands **under the code box**; the server says
`code_incorrect` for a wrong code and for an address nothing was sent to alike, and the sentence
cannot tell them apart either. **Expired, used and locked each have their own sentence** in the
banner, told only to someone who typed the right code, and the expired one says to ask again: _No
email? Ask again_ sits under _Continue_ and carries the email back to the first form.

**The ticket rides in the route, and the refusals are worded by the way in.** A right code buys a
fifteen-minute ticket, and _Set a new password_ is pushed over the code screen with it as a param —
navigation state, gone with the screen, and never the keychain's or a store's, since it opens one
act and outlives nothing. The link's token arrives the same way because a link is a route. Both are
parsed before anything trusts them (URL-safe base64 to the server's own cap); one that cannot be one
redirects to the screen it comes from — the code screen for a ticket, the email form for a link.
The one screen serves both, and they differ in where to go when it did not work: a ticket that ran
out is _That took too long. Enter the code again._ with _Enter the code again_ going back to boxes
that still hold the code, which buys another ticket because a claim is not a use; a link has no
screen under it, so its way out is _Ask again_. **The code's way out follows the refusal**
(`resetWayOut`): once a refusal says the email itself is spent — expired, used, locked, not found —
going back would meet the same refusal one screen earlier, so the link becomes _Ask again_ with the
address carried (the ticket's route carries it beside the ticket for this). Expired, used and
locked say _that code_ or _that link_ accordingly.

**Setting it is signing in, and the toast is the _done_.** The server signs out everywhere and
answers this session's pair (ADR-0185 §7); `setNewPassword` hands it to `beginSession` exactly as
`signIn` does, and the `(auth)` guard sees the session begin and gives it to the entry gate — the
flow never navigates into the app itself, so an account that owes onboarding goes there. With no
screen of the flow left to say it on, the mutation's own `onSuccess` raises _New password set. Any
other phone is signed out._ — it says the second half because a person whose other phone goes
quiet should know why. That other phone needs nothing new: its next request is `401
access_token_revoked`, the rotation meets a revoked refresh token, and the session ends on the
sign-in screen. **No mutation here is retried**: a retried ask spends one of three emails an hour
on a request nobody saw, a retried claim of a wrong code is a wrong code nobody typed, and a
retried set whose answer was lost meets `credential_used` about a password that is, in fact, set.

**One password rule, on both forms that choose one.** _Set a new password_ asks for the rule every
account shares — 8 to 128 characters with a letter and a digit — and states it under the box before
anything is typed, the nickname's shape. Sign-up checked only the length, and a letters-only
password there reached the server unchecked; it now shares the schema, the sentence for whichever
half is missing, and `PasswordPairFields`, so **sign-up draws the rule line under its password box
too**. The server's `password_too_weak` says the rule itself, under the box.

**Not seen on a device**: the four new screens, the `lead` line under a title, the _Forgot
password?_ link's place between _Sign in_ and _New to Raketa?_, and sign-up's new rule line.

**The signed-in player carries the account's profiles** ([#516](https://github.com/Raketa02/Raketa/issues/516),
ADR-0185 §2). `GET /users/me` answers `MeResponse` since #508, and `me()` reads it: `AuthenticatedUser`
gains `profiles` — `actsAsPlayer` and the clubs it `administers`, by id and name — for the entry
gate's first read, kept for `hasPlayerProfile`'s reason. The pending invitations are not carried until
the invitation sheet (#518) draws them. **`useSignOut` is public** for one caller outside this feature,
the administrator area, which signs out an account its club removed; the sequence stays this
feature's.

**_Start playing_'s first step is this feature's, and so is the naming that follows it**
([#517](https://github.com/Raketa02/Raketa/issues/517), ADR-0185 §4–§5). An account an Invitation
opened runs a club's groups and has never been asked its age, so the first time it acts as a player
it gives **the Adult attestation**: `StartPlayingScreen`, `POST /users/me/adult-attestation` through
`attestAdult` and `useAttestAdult`. It lives here on the naming's precedent — the act is the users
context's, on the account — and asks with **sign-up's own box, claim and refusal** (`TickBox`,
`ADULT_LABEL`, `ADULT_ATTESTATION_MISSING`; the schema's `adultAttested` field is shared), never ticked
on arrival, with _Continue_ never disabled by it. **Not retried.** Like the naming, it **writes and then
re-reads**: _acts as a player_ goes into the cached player at once and a fresh `/users/me` is awaited,
so the gate reading the cache next already moves the account on, and the screen replaces itself with
`/`. **Two addresses, one screen**: the administrator's You tab pushes it inside its area (so _back_ is
the tab), and the gate redirects an account with no profile at all to `START_PLAYING_STEP`, where
nothing is behind it: no back is drawn, and **_Sign out_ is drawn under _Continue_ instead**, a link,
because signing in again must never be a dead end and a person who does not want to play has no other
screen with a way out. The screen reads which from `router.canGoBack()` as it opens. **Named in full
is one rule, `domain/naming.ts`** — a name and a nickname — which the gate reads through `types.ts`
(`namedInFull`) and the naming step beside it (`heldNameWithoutNickname`).

**The naming asks only for what is missing** (ADR-0185 §4). An account that holds a name and no
nickname — the club's name — sees the nickname's box alone, and the sub-line _People will see you as
Marta Nowak. Pick a nickname to go with it._; the form opens holding that name and sends it with the
nickname, so the naming stays one act carrying both. Every account sign-up creates holds neither and
sees both boxes. **Not seen on a device**: the attestation step, and the naming with one box.

**_Have an invitation code?_ and _Set your password_ are _Forgot password?_'s pieces asking for an
invitation's** ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories 113–116 and
121, ADR-0184 §2–§4). The link sits under _Forgot password?_ on the one sign-in screen, carrying the
email typed there. `/invitation` takes **the email and the code** — read the server's way, its length
checked first, `invitationCodeSchema` being `resetCodeSchema` since it is one credential machinery —
and `POST /invitations/claim` answers a ticket, which pushes **_Set your password_** at
`/invitation/password` with the ticket and the email in the route. **The email is drawn in its box and
locked** (`editable={false}`, the busy shape and never 6.13's `disabled`, which says _refused_): the
invitation is to that address. Sign-up's two password boxes and the rule follow, and
`POST /invitations/password` creates the account — the club's name, no nickname, no attestation — or
gives back a password the club reset, and **answers this session's pair**, which `beginSession` takes
exactly as sign-in's; the `(auth)` guard hands it to the gate, which opens the area of an account that
only administers. **No toast**: the area is the _done_. By the email's button the path is
**`/invite/<token>`** (`INVITATION_ROUTES.link`, what #520 opens), and **the token is validated before
anything is drawn**: `POST /invitations/by-token` is read first, and only a link that still works
draws the form, with the email the server read. While the read is out the frame and its title stand
alone, so no form flashes; a spent link says why in the sentence the set would have used, and a read
that could not be made offers itself again — except `credential_not_found`, which a second read will
not change. A token or ticket that cannot be one redirects to the code form, the other door.

**Every refusal has its own sentence, and an expired invitation names who to ask**
(`invitationPresentation`). A wrong code lands under the code box, in the auth-wide sentence.
_Expired_, _used_ and _locked_ are the banner's, worded by the way in (_that invitation_, _that
link_), and **expired says _ask the club to send a new one_** where _Forgot password?_ says _ask
again_: an invitation is the club's to send. **`sign_in_to_accept` is _This email already has an account
— sign in to accept._**, and _Back to sign in_ sits under every form of the flow. The way out of _Set
your password_ follows the refusal, `resetWayOut`'s rule (`invitationWayOut`): back to the code while
it can buy another ticket (`ticket_expired`), sign in once the invitation is spent. No mutation here is
retried, for #515's reasons. The link's four states are spelled in `domain/vocabulary.ts` and held equal
to the wire's in `mappers/wireVocabulary.ts`.

**The account's profiles carry the invitations it is offered, and accepting one is this feature's
act** (#518, ADR-0185 §2). `AccountProfiles` gains `pendingInvitations` — administrator id, club,
expiry, soonest first, as the server lists them — mapped once (`toAccountProfiles`) for `/users/me`
and for `POST /invitations/{administrator_id}/acceptance`, whose answer is the same shape: so
**`useAcceptInvitation` writes that answer into the cached player and re-reads nothing**, and the
switcher the sheet becomes draws both profiles from it. The readers that only care what the account
_holds_ — the gate, the switcher, a removal — take `HeldProfiles`, the two fields without the
invitations. The sheet itself is the administrator feature's ([`administrator.md`](administrator.md)).

**The last profile is this feature's value on the phone** (#518, ADR-0188 §2): `ProfileChoice` —
Player, or one club's administrator profile — kept as `player` or `administrator:<club>` under the
store's third key, `lastProfile`, and read back by `profileChoiceFrom`, for which anything else is
nothing chosen. `useLastProfile` is the Play segment's shape (read once per account into the Query
cache, `networkMode: 'always'`, never stale) and `useKeepProfile` writes the cache first and the phone
second. Auth owns it because the profiles are auth's and three writers need it: the switcher, a
removal, and **the Adult attestation, which now keeps Player** — starting to play is choosing Player,
and an account that wore a club's profile last would otherwise be sent back to that club's area the
moment the gate took the next step.

**Not seen on a device**: the two new screens, the locked email box, and the third link under Sign in.
