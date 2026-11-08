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

**A player is known by their nickname, and the naming asks for it alone**
([#728](https://github.com/Raketa02/Raketa/issues/728),
[ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3, superseding ADR-0171
and the two paragraphs above where they speak of a Name). _How should people see you?_ keeps its
title and has **one box, _Nickname_**: `namingSchema`, `Naming`, `useNamingForm` and the request are
`{ nickname }` and nothing else, and `AuthenticatedUser` carries `nickname` alone — `/users/me` stopped
serving `name`. **No hint under the box**: the handle's rule (_Use letters, numbers, and . _ - only —
no spaces._) is the schema's refusal and is drawn only as the box's error, when what was typed breaks
it; the other refusals are unchanged, _That nickname is taken. Pick another._ among them. The box's
`accessibilityHint` that carried the rule went with the visible hint — a listener hears the rule
when a sighted reader sees it. **The You row is _Nickname_** (`NicknameRow`, `NicknameScreen`,
`nicknamePresentation`): its line is the nickname whole and without an @, and its screen is the
same one box under the tab's chrome. **The route keeps `/you/name`**, as the act keeps
`PUT /users/me/name` (ADR-0199, _Neutral_) — and because the shell names the route, one by one,
for its push transition. **Named is holding a nickname** (`domain/naming.ts`'s `named`, which the gate reads through
`types.ts`). **An account an Invitation opened holds no player name** — the one its club typed stays
the Administrator's (§4) — so `heldNameWithoutNickname` and the step's one-box mode are gone, and
what tells the step such an account is `runsAClub` — `/users/me` says which clubs an account
administers and not how it was opened, so a club profile is the phone's one sign. It reads
_Pick a nickname — it's how players will see you._ under the title; every account sign-up creates
reads the title alone. `theNaming.test.tsx` and `nicknameFromYou.test.tsx` walk both. **Not seen on
a device**: the one-box step, the invitation line, and the You row's new title.

**The tester mark is not read** ([#576](https://github.com/Raketa02/Raketa/issues/576)). It was
carried as `AuthenticatedUser.isTester` for one reader, feature-flag evaluation (#479, ADR-0180
§9), which left with the flags. `/users/me` still sends `is_tester` until the backend drops it
(#581), and the mapper drops it as it drops `is_admin`.

**_Forgot password?_ is four screens and a toast, made of the sign-in screen's pieces**
([#515](https://github.com/Raketa02/Raketa/issues/515),
[ADR-0184](../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
§5). It sits under the Sign in button on the one sign-in screen players and administrators share,
and walks: the email (`/forgot-password`, opened with whatever the sign-in box held), a neutral
confirmation (`/forgot-password/sent`), the email and the code (`/forgot-password/code`), and
_Set a new password_ — by a claimed code at `/forgot-password/new-password`, or by the email's
link at `/reset/<token>`, the path the email's button names and the one #520 opens from an
incoming link. **Nothing is drawn twice**: the sign-in screen was taken apart into `AuthFrame` (the
paper, the scroll that keeps a form reachable over the keyboard, _RAKETA_ over the title, and an optional `lead`),
`EmailField` (the five props that make a box an email box), `AuthLink` (the 44pt text link, by
`href` or by `onPress`) and `PasswordPairFields` (sign-up's two revealable boxes and the rule), and
sign-in, sign-up and the four new screens are each those pieces asking one thing. The route paths
are `RESET_ROUTES` (with `askForResetHref` for every way back to the email form), the recovery's
sentences are `resetPresentation`'s, and the words sign-in and sign-up still wrote inline moved to
`authPresentation` on the way past — a label a piece draws on six screens is copy with six readers.
The text link's press is 6.6's `.7`; the two screens it came from drew `.6`, which that table does
not have.

**The keyboard moves the scroll, never the form** (#529, 2026-10-02; `AuthFrame`). On iOS every tap
that moved focus or pressed _Show_ with the keyboard up made the screen jump. The form was centred in
what a `KeyboardAvoidingView` left above the keyboard, and iOS changes the keyboard's height while it
is up: the bar over the keys is swapped per field (the email's suggestions, saved passwords, _Use
Strong Password_) and again when a password's secure entry is turned off or on. Each swap re-padded the
view from JavaScript and slid the centred form by half the difference. Android never did it: its
avoidance is the window's, and `KEYBOARD_AVOIDANCE` is off there. **The scroll now takes the keyboard
natively** (`automaticallyAdjustKeyboardInsets`): the form is laid out once against the whole screen,
the keyboard changes only the scroll's bottom inset on its own curve, and the scroll moves only as far
as it must to keep the field being typed in above the keys. The cost on a short screen: _Sign in_ may
sit under the keys, where the password's _Go_ sends the form and a drag puts the keyboard away. **Not
yet seen on a device.**

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
_Superseded by #728 (ADR-0199 §4): no account holds a player name, the naming is one box for
everybody, and an invitation account reads its own line — see the nickname paragraph above._

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

**The two email links are opened from outside the app by [`links`](links.md)** (#520). `invite/<token>`
and `reset/<token>` stay under `(auth)`: nobody signed in lands on _Set your password_ or _Set a new
password_ from the link itself, and a signed-in phone is handed by the guard to the gate, where the links
feature asks first — the invitation's sheet naming the address it is for, the reset's asking to sign out.
**The reset route lets the held link go** (`useResetLinkOpened`), so the session its password begins is
not asked about the link it just used; the invitation route keeps it, so an existing account that signs
in from _Set your password_ is offered the invitation. `InvitationLink` now keeps the club's name from
`by-token`, so a link re-offers only its own club's invitation, and it is exported for that feature
with `useInvitationLink`, `LINK_STATE_MESSAGE`, `invitationErrorMessage`, `SIGN_OUT` and
`authErrorMessage`: a spent link opened signed in is said in the words _Set your password_ would have
used, and the sheets' _Sign out_ is this feature's button. A malformed token no longer reaches
either route from outside — the reader ignores the link — so their redirects to the code form and the
email form now guard only the app's own navigation.

**A sign-out lets the phone go first** ([#559](https://github.com/Raketa02/Raketa/issues/559)).
`signOut(phone)` — handed the push port by `useSignOut` — asks the phone for its push token, only on
a phone that may show a notice, and `POST /players/me/devices/removal` with it in the body, **before
the revoke**: both need what `endSession` destroys, the removal the session and the revoke the
refresh token. Best-effort, as the revoke is — a player on a train still leaves. `removePushDevice` is
in `auth`'s api because the act is the sign-out's; registering the phone is `notifications`'. A session
that ends by itself — a refused refresh — cannot sign a removal, and that phone stays registered to
the last player until the next sign-in on it (`notifications.md`'s call 7).

**The naming leads to the profile steps** ([#730](https://github.com/Raketa02/Raketa/issues/730),
ADR-0200 §1). The step still hands the next destination back to the gate, which now answers _the
six steps_ for an account sign-up created; the _Continue_ hint that promised _a few questions to
find your level_ says _Next, what kind of player you are_.

**The launch stops waiting after five seconds, and leaves what it learnt where the gate reads
it** (2026-11-07). A launch with a stored session validates it with `/users/me` behind the splash,
and on a connection that reaches nothing — a weak signal, a captive portal, a server that is not
there — that read waited out the whole fifteen-second request timeout, after which the entry gate
asked the same question three more times behind an empty screen: about a minute before a word.
The read is now `fetchCurrentUserAtLaunch`: the one `currentUserQuery` definition, asked through
the cache with the **`launch` timeout class** (5 s), no retry, and `networkMode: 'always'` — a
paused launch read would hold the splash until the connection came back. Giving up early costs
nothing but the wait, because an unanswered validation keeps the session. Through the cache so
that both answers land where the gate looks: the player, which the root layout used to seed by
hand, and **the failure, which is now the gate's first answer** ([`onboarding.md`](onboarding.md)).
`restoreSession` takes the read as its argument — a use-case may not know Query — and gained one
branch: a refresh rejected under the read ends the session, and the teardown cancels the read with
it, so what arrives is a cancellation rather than the 401. The session machine already says
`unauthenticated`, and the launch says the same rather than opening the session again. **Not
covered**: a launch that starts on an expired access token refreshes with the ordinary `request`
budget — the rotation is single-flight and shared, so there is no caller to take a class from.
**Not seen on a device.**

**Sign-in is drawn on the stage, and nothing it does changed**
([#784](https://github.com/Raketa02/Raketa/issues/784), PRD #783; design system 12.2). A dark hero
over the top four tenths of the window — the _Raketa_ wordmark in its top-left corner and _Your next
game is only one swipe away._ at its foot, the deck dealt between them since #786 — and a paper
sheet with rounded top corners over it, holding the form. Every control keeps its target and what it
carries, the refusals keep their sentences and their sources, and **Sign in** still fires on the
button and on Go and reads _Signing in…_ while busy. The mocks' _Rakieta_ is read as **Raketa**
(ADR-0187 §8). Design only: no request, schema, use-case or route changed.

**The stage is a new frame beside `AuthFrame`, not a change to it** (`AuthStage`, `StageHero`,
`StageGround`; the keyboard props #529 put on the scroll are `FORM_SCROLL`, shared by both frames). The eight other auth screens — the _Forgot password?_ flow, _Have an invitation
code?_, _Set your password_ and the two links — keep the paper frame and its _RAKETA_ eyebrow,
because a short recovery task is not crowded by a hero. On the stage the hero's wordmark replaces the
eyebrow, so the sheet opens on the title alone. Sign-up moved onto it with #785, below.

**The sheet scrolls and the hero stays put.** The hero is drawn behind the scroll at 0,41 of the
**window**'s height, and the scroll's content opens with that much transparent room before the
sheet; a short phone, large text or the keyboard slides the sheet up over the hero, which does not
move — Android's window shrinks for the keyboard, and a hero sized by the layout would shrink with
it. **#529's native keyboard inset is kept**: `automaticallyAdjustKeyboardInsets` on the scroll, so
the form is laid out once and the scroll moves only as far as it must to keep the focused box above
the keys. No bounce, so the sheet never lifts off the bottom onto the night. The insets come from the
root's provider through its context — known since the first frame, so the wordmark is clear of the
status bar first time — and are none where a suite draws the screen with no provider.

**The hero is a picture: hidden from screen readers, untouchable, and its words capped.** ADR-0198:
the form is the screen. The wordmark and the headline grow with the OS text size only to
`size.stage.textMaxScale`, the tab bar's mechanism — derived in `stageTextCap.test.ts` as the
largest step at which every stage headline stays within three lines on a 320pt phone (1,7 with
sign-in's alone, 1,6 since sign-up's joined it) — because the hero's room is fixed and the picture
takes what its words leave. The form is not capped; it scrolls.

**The status bar is light only while sign-in is the screen in view.** A stack keeps sign-in mounted
under _Forgot password?_ and the invitation screen, and a light bar drawn for as long as it is
mounted put white icons on their paper. `useScreenInView` reads the navigator's focus **in the route
file** and hands it to the screen as `inView`: the navigator's hooks throw outside a navigator, and
the auth suites draw the screen on its own, where it is the screen in view. The sign-in loop (#787)
will stop and start on the same value. **The bar is always over the night**: a band of the hero's
ground the status bar's height is drawn over the scroll, so a sheet scrolled all the way up — a short
phone, the keyboard, large text in the uncapped form — slides under it rather than putting paper
under white icons.

**The form, top to bottom**: _Sign in_ (the stage's large title); the server's banner when there is
one; _Email_, **empty, with _you@example.com_ as its placeholder** so the keychain's autofill still
offers the saved address; _Password_ with **Show**/**Hide** inside the box; **_Forgot password?_,
quiet and right-aligned straight under the password box** (`AuthLink`'s `quiet`: `muted`, at the end
of its row) — where the problem is, rather than under the button; **Sign in**, the full-width primary
button at the boxes' own height; a thin _or_ rule; **_I have an invitation code_**, a white
outlined box with a small coral dot; and _New to Raketa? Create an account_ at the sheet's foot.

**_I have an invitation code_ is a statement on a link drawn as a button**: 6.1's `secondary`
button at the stage's height with `Button`'s two new options, **`role="link"`** and a coral **`dot`** before its
words. It was _Have an invitation code?_ on a text link; the screen it opens keeps that question as
its title. It opens that screen carrying the email, exactly as before, and a screen reader still
meets it as a **link**, after _Forgot password?_ among the sign-in screen's links, as the invitation
suite has always held — it opens a screen rather than acting. Both options are `Button`'s rather than
a feature's copy of its look (`src/shared/ui/README.md`); the dot is the product owner's, kept
against design system 1.2.

**A box's own refusal is drawn on its label's row**, right-aligned, and the box keeps its red border:
_Enter your email address._, _That doesn't look like an email address._ and _Enter your password._,
today's sentences from today's schema. It is 6.13's new opt-in, `errorOnLabelRow`, so the form does
not shift down a line under a refused box; a sentence too long for the row wraps in its own column.
**Every other field in the app keeps its message under the box.** The banner — wrong credentials, no
connection — stays between the title and _Email_: a refusal about the whole form, above the whole
form.

**The boxes and buttons are the mock's, on the stage only** — the product owner's ruling on
2026-11-08, when the review found them drawn in the app's own look: the mocks win on a look. The
shared field's opt-in **`stage` look** draws a grey sentence-case label, a 48pt box holding a 14pt
value, and a sentence-case **Show**; `Button`'s **`stage` size** stands both buttons at that height.
Sign-in's two boxes and two buttons take them, sign-up's three boxes and its button since #785, and
**every other field and button in the app keeps its look** — the eight other auth screens among
them. It is the same build in every environment: nothing here is chosen by `EXPO_PUBLIC_ENV`.

**Not seen on a device**: the whole stage — the hero's ground and glow, the sheet over it on a short
phone with the keyboard up, the label-row refusals, the light status bar, and the hero's words at the
largest text size — on iOS and Android.

**Create an account is drawn on the same stage, and nothing it does changed**
([#785](https://github.com/Raketa02/Raketa/issues/785), PRD #783; design system 12.2, mocks 4 and
6). The hero is sign-in's — the wordmark exactly where sign-in has it — with _Play ranked. The
competition starts with you._ at its foot, and the podium arriving in #788. The sheet holds the
title alone, the banner, _Email_, _Password_ with the rule under it, _Repeat password_, _I am 18 or
over_, **Create account** and _Already have an account? Sign in_ at the foot. The same request goes,
the same refusals come back from the same sources, the box still never arrives ticked, and the
auth flow suite's sign-up cases pass untouched. Its headline is longer than sign-in's, and at 1,7
it wraps a fourth time on a 320pt phone, so the derived cap is now **1,6** for both screens.

**Each box opens empty with a placeholder**: _you@example.com_ in _Email_, as on sign-in, so the
keychain's autofill is not fighting a value; _At least 8 characters_ in _Password_; _Once more_ in
_Repeat password_. A placeholder is a hint that goes the moment somebody types, never the rule and
never the label — the label above the box stays the box's name for a listener.

**The password rule is under the box all the time.** _Use 8 to 128 characters, with at least one
letter and one digit._ sits under the password box in small grey type before anything is typed and
after a refusal. Off the stage — _Set a new password_ and _Set your password_, which keep their
frame — a refusal under the box still takes the rule's line; on the stage every box's refusal is
drawn on its label row, as sign-in's are, so the rule has nothing to give way to and the form does
not shift under a press. It is `PasswordPairFields`' opt-in `stage`. The server's _That email
already has an account. Sign in instead._ is the email box's, on its label row; the banner stays
between the title and _Email_; the 18+ refusal stays under the tick box.

**The tick box is the mocks' rounded square**, 22pt where it was 20, the corner the cell's 6 —
design system 6.11's block had said a circle, and the code had always drawn the square. Checked, it
fills `ink` with a white tick, and the whole row is the target. _Start playing_ draws the same box
and follows it. The friends picker's circle borrowed the size and keeps its 20.

**Sign-in and sign-up cross-fade, and _Sign in_ goes back.** Sign-up asks the native stack for
`animation: 'fade'` (`(auth)/_layout.tsx`): a screen's animation is the one it is pushed and popped
with, so _Create an account_ fades sign-up in over sign-in and the way back fades it out — the frame
seems to stay while what is in it changes. Sign-in keeps the platform's slide, because it is also
what a recovery or invitation screen opened from an email link puts in its own place, and that move
is not this one. _Sign in_ on sign-up is `dismissTo('/sign-in')`, so it returns to the sign-in
underneath rather than pushing a second one (the stage suite holds that only one is mounted and
that nothing is left to go back to); opened with nothing under it, it puts sign-in in its place.
Android's back pops sign-up the same way. The status bar stays light: each screen draws its own
while it is the one in view. Every other auth screen keeps the platform's slide.

**Not seen on a device**: sign-up's stage on iOS and Android — the sheet over the hero on a short
phone with the keyboard up, the rule under the box beside a refusal on the label row, the 22pt box,
the cross-fade both ways (and whether iOS's edge swipe back still works under a fade), and the hero's
words at the largest text size.

**Sign-in's hero deals three miniature game cards** ([#786](https://github.com/Raketa02/Raketa/issues/786),
PRD #783; design system 12.2, mock 2), fanned between the wordmark and the headline. **Front,
straight**: a padel game waiting for a fourth — _Seat open · ⏱ 21 h 00_, `karol.t` 2,75, `ania.k`
2,68 and `kuba.w` 2,80, each _paid_, the reader's dashed volt seat _You complete it_, _91%_ over
_karol.t + You_ | _ania.k + kuba.w_, and _Sat 16:00 · Ogrody 33_ with _27 zł_ in volt. **Left,
turned**: a tennis single, _Picked for you_ — `marek.z` 3,15, _74%_, _Thu 19:00 · Ogrody 33_.
**Right, turned**: a squash _Fill in · seat open_ — _⏱ 2 h_, one empty seat, _stas.w + ola.m_,
_30 zł_. The tiles show nicknames, not the mocks' _Karol T._ (ADR-0199 §1), chosen so their letters
are the mocks' — KT, AK, KW, MZ, SW — for the splash (#787) and the podium (#788) to draw. Every name,
figure and line is `stageHeroCopy.ts`'s, the cast's posters with them, so one person is one face on
every picture the hero draws; what the front card hides — the single's second tile, the squash
game's `ola.m`, its figure and its line — is filled in plausibly so the drawing is whole.

**The hero is an illustration copied from the game card, not the game card.** `MiniGameCard` is the
real card's look — the ribbon with its status and clock, the 2 × 2 tiles with a poster, the nickname
and the Level on the scrim, the dashed volt seat, the forecast's figure and two-sided bar, the
booking strip — redrawn in auth with plain props from what shared UI already makes public: the
poster (`CourtPoster`), the balance bar, the theme. **The live Games deck is not made public and not
changed**: auth importing `proposals` would be an import cycle, and it would bend a live card around
a sign-in picture. **The cost: a later redesign of the game card does not reach the hero by itself,
so whoever changes the card checks the hero** (`MiniGameCard.tsx`, `stageDeckPresentation.ts`);
`proposals.md` and design system 7.22 say so from the card's side. Where mock 2 draws the card
differently from the app the mock wins, because this is a picture of the mock: no _vs_ line and no
week grid, a one-line booking strip bordered in the booked court's volt stroke on all three, the
reader's seat with its words alone, and a green ribbon on the Fill in. **One departure the other
way**: the tile rows are equal, as the live card draws them, where mock 2 draws the top row about
half the bottom's height — a top row that short would be its scrim and nothing else.

**Drawn at one size, then scaled into the room.** The miniature is drawn at `size.stage.card` —
twice mock 2's miniature, because its words measure the real card's own roles at about half — and
the fan (`size.stage.fan`, the back cards either side, a little lower, turned outwards) is scaled
whole into the room the wordmark and the headline leave (`stageDeckGeometry.ts`). That room is
**measured**, because a short phone, a tall one and a headline at the text cap's three lines each
leave a different one; on a 390pt phone the deck draws at a little under half its size, smaller on a
375 × 667 one, and it never runs over the headline. It is never drawn larger than its own size, and
nothing is drawn until the room is known. The cards' words take the hero's text cap and one line
each, so a large text size cuts a name rather than pushing a card's parts out of its box.

**The deal.** When the screen opens the three sit stacked exactly on top of each other for
`motion.stageDeck.stacked`, then the two back cards slide to their turned places over
`motion.stageDeck.deal`, `easeDecel`, while the front card stays put. It plays once, when sign-in
mounts; the swipe and _It's a game!_ that follow, and starting again from the deal when sign-in
comes back into view, are the loop's (#787). **Under reduced motion or a running screen reader** —
the app's collapsed-presentation rule — the cards are dealt at once and nothing moves: from the
first frame under reduced motion, which the root already knows, and the moment the OS answers for a
screen reader, which is a promise that lands well inside the stacked beat. React Native's `Animated`
on the native driver, the yes screen's choice. `stageDeck.test.tsx` drives the clock through the
deal, both collapsed cases and the fit; the hero stays hidden from screen readers, so its queries
opt into hidden elements.

**Not seen on a device**: the three cards and the deal on iOS and Android — the posters and the
dashed seats at half size, the turned cards' edges, the fit on a short phone and with large text,
and the headline under the deck.
