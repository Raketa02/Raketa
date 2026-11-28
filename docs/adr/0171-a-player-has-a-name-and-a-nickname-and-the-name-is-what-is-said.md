# ADR-0171 — A player has a name and a nickname, and the name is what is said

- **Status:** Superseded by [ADR-0199](0199-a-player-is-known-by-their-nickname.md) — **in full, 2026-11-03**: the Name is retired, and the
  Nickname is what every screen says, without an @. An account an Invitation opens holds no player
  name. The text below is kept for why a name once looked right; where it and ADR-0199 disagree,
  ADR-0199 decides.
- **Date:** 2026-09-15
- **§2 and §3 amended 2026-09-25 by [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §4**: an account an Invitation created carries the club-typed Name and no Nickname, so the naming step asks only for what is missing, and the gate's first destination reads *not named in full*. The naming stays one act.
- **The You-tab edit this record did not decide is decided by [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §7** — the same
  act, from the *Name* row, refused by the server with the same code.
- **Supersedes one sentence of [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)
  §4** — *"every sentence naming somebody uses the whole handle or names nobody"* — with ***the
  whole name or nobody***. §4's argument stands whole: the client may never *invent* a familiar
  form, and nothing here lets it. **Amends §2's closed list by a rename**: the card carries the
  **name** where it carried the nickname, and grows nothing. [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
  §3's initials stay the one derived form, now cut from the name.
- **Amends [ADR-0090](0090-onboarding-per-player-checkpoint.md)'s entry gate by one destination,
  first in its order**: *no name → the naming step*. §3 says why it is read before the run, and
  why it passes the glossary's test the way the profile did.
- **Supersedes the seed catalog's argument** — `backend/app/seeds/catalog.py`, on `FIRST_NAMES`:
  *"`First.Last` and not `First Last`, because `Nickname` is `^[A-Za-z0-9_.-]+$` … a fixture is not
  where it gets reopened."* It was right, and this is where it is reopened (§5).
- **Renames one field on the wire, everywhere it names another player**: the `nickname` that
  [ADR-0141](0141-a-game-names-its-court-and-the-court-is-the-gate.md) §1,
  [ADR-0143](0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md),
  [ADR-0148](0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md) and
  [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) put on a seat, a member or
  a person is **`name`**. Nothing else in those records moves; their tests — *a seat with no
  nickname is still a person who was on the court* — read the same with the word swapped.
  [ADR-0124](0124-the-matcher-gates-account-state-never-age.md)'s description of the registration
  command — *`email, nickname, password`* — is now *email, password, attestation*; its decision is
  untouched.
- **Where the superseded sentence is quoted, it reads through this record.** The specs are not
  rewritten: `the-play-screens.md` (*The record block* — *"there is no name in this platform"*),
  `the-play-components.md` §5, `the-loop-screens.md` §3.3 and §6, `the-loop-components.md` §2.1
  and `player-record/the-decisions.md` §0 say *the whole handle* where the rule now says *the
  whole name*, and `the-words.md` says so once in §15 for the rest of that file. The client's
  own copies — `docs/features/play.md` and `playerName.ts`'s docstring — are
  [#451](https://github.com/Rakieta02/Rakieta/issues/451)'s; the backend's `PlayerHandles` port
  and its `CLAUDE.md` are [#450](https://github.com/Rakieta02/Rakieta/issues/450)'s.
- **Leaves standing** [ADR-0157](0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
  — the stem's word break already includes a space, so a name's stem is the same rule with a
  second character finally exercised (§4); [ADR-0002](0002-event-sourced-user-aggregate.md) — the
  `User` is one event-sourced aggregate and gains one event; and
  [ADR-0170](0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md) — the intro is where
  a person *speaks*; the name is where they are *named*, and the Consequences say why the
  intro's contact fence is not copied onto it today.
- **Does not decide** editing the name or the nickname from the You tab after onboarding (the act
  is repeatable; the screen is a follow-up), searching players by nickname, a first-name form
  anywhere, or migrating accounts (only `local` runs; a reset seed is the migration).
- Settles [#447](https://github.com/Rakieta02/Rakieta/issues/447), built by
  [#450](https://github.com/Rakieta02/Rakieta/issues/450) (backend) and
  [#451](https://github.com/Rakieta02/Rakieta/issues/451) (player app). Grilled 2026-09-15, session
  *left-alone*, rounds 5–6 of the grilling that also produced the called-off spec
  ([#448](https://github.com/Rakieta02/Rakieta/issues/448)), which is written on this vocabulary and
  lands after it. The mock every sentence was read on:
  [Diego Left](https://claude.ai/artifact/N7wHrEwhWmFvuJE8B4kRYn).

## Context

**Paula opens Chats and reads *Diego.Fabregat left*.** Rafa's row reads *Pablo.Sabater said no*.
The dot is not a seed quirk. A **Nickname** is a handle — 2–64 characters of `[A-Za-z0-9_.-]`,
enforced by the value object and by the sign-up form (*"Use letters, numbers, and . _ - only — no
spaces."*) — and it is the only name a player has. `users` holds an Email, a Nickname and a
password hash; there is no first name, surname or display name anywhere on the platform, and
every row, sentence, sheet, toast, seat label and poster draws `nickname`. So the most
name-shaped thing a seeded player can be called is `First.Last`, and the most name-shaped thing a
real player can type at sign-up is the same. The seed catalog said so in its own defence — *the
dot is the most name-shaped thing a legal nickname can be* — and declined to reopen the users
context's rule from a fixture. It was right to decline; this record is where the rule is reopened.
The author's verdict: *"Having names with a dot separated is not good user experience."*

**Two more things follow from the handle being the name.** It has to be **unique**, so the day two
Diego Fabregats sign up the second is told the name is taken — right for a handle, strange for a
name. And it is asked at **sign-up**, beside the password, where a person is choosing credentials
rather than saying who they are; a sign-up refused for a taken handle is a sign-up refused for a
reason that has nothing to do with the account.

**What stands behind the current shape, and what it actually depends on.** ADR-0107 §4 forbids
the client to *invent* a familiar form: the prototype's `p.n.split(' ')[0]` over a real name
produced *Marek* for a person who never gave the platform that word. ADR-0157 admitted a **stem**
— a prefix of the handle cut at a character its owner typed, drawn only in a box — inside that
rule; ADR-0167 §3 argued two initials over a poster as the one **drawing** exempt from it, with a
four-sided fence; `the-words.md` §15 drew the line at truncation — *a seat label may truncate
visually; a sentence may not, and a spoken name never does*. Every one of those was argued from a
handle, because a handle was all there was. **None of them depends on the name being a handle.**
What each depends on is that the platform says what the player gave it, whole, and derives
nothing a sentence could address them by. A name the player typed themselves satisfies that
exactly as a handle did.

**The alternatives, and why each was ruled out:**

- **Let the nickname hold a space.** One field playing two parts: the thing that is unique and the
  thing that is said. The second Diego Fabregat is still told his name is taken, and a handle with
  a space in it cannot be written `@…`, which is the form a handle exists to take.
- **A name and no nickname.** Two people named *Ania Kowalska* are then indistinguishable on the
  one screen where it matters — the record a friend opens to see whether it is *their* Ania. The
  handle is what tells them apart, and it is what a search by nickname would find the day one is
  built; the term is kept for that, not for a sentence.
- **Both at sign-up.** Sign-up is credentials. Asking *who are you* beside *choose a password*
  conflates two moments, and it is the first thing a new player meets. Onboarding already opens by
  asking about the person; the name belongs at its head, where the questionnaire that follows can
  address them by it.
- **The name on the Player profile** ([ADR-0089](0089-player-profile-context-event-sourced.md)).
  The profile is onboarding's *second* part, committed in one POST at its end (ADR-0090); the name
  is needed before the questionnaire, and the nickname's uniqueness is a `users` fact read from the
  `users` projection ([ADR-0018](0018-aggregate-repositories-over-the-event-store.md)). Splitting
  the two across contexts would put one act's refusal in a context that cannot raise it.

## Decision

### 1. Two terms: the name is what a player is called, the nickname is what is theirs alone

**Name** is a new domain term: *what a player is called* — free text, **2 to 64 characters after
trimming, runs of whitespace collapsed to one space, never unique**. *Diego Fabregat*, *Diego*,
*Dieguito* and *Ania Kowalska* are all names; two players may share one. It is a value object in
`users`, and it is checked against nobody.

**Nickname** keeps its definition and its rule — 2–64, `^[A-Za-z0-9_.-]+$`, unique across the
platform — and gains one sentence: **it is a handle; it is shown as `@nickname` under the name on
a player's record and on their own You tab, and it is said nowhere.** The refusal for a taken one
is today's `NicknameAlreadyTaken`, a domain conflict.

The two are asked together, under one title, and the name is asked first: the step is
**`How should people see you?`**, its fields are labelled **`Name`** and **`Nickname`**, the
nickname's rule is stated under its field in the sign-up form's existing words, and a taken
nickname is refused in words under the field. The client writes the sentences; the backend
names the code ([ADR-0022](0022-kernel-negative-space-and-constant-homes.md)).

### 2. Sign-up asks for credentials, and the naming is one act

**`POST /api/v1/users` is email, password and the Adult attestation.** The nickname leaves the
payload, and a `User` is created **unnamed**: `UserRegistered` (`users.user_registered` / v1)
loses its `nickname`. It stays v1 because a version exists to tell two stored shapes apart and
only one will ever be stored — only `local` runs, its store is disposable, and the reset seed is
the migration (the Consequences name the day that reasoning stops being available). `RegisterUser` still
refuses without the attestation before it reads anything, and now reads only the email.

**One act names a player: the naming.** `PUT /api/v1/users/me/name` with `{ name, nickname }`,
admitted for the authenticated player, **repeatable** — a later change is the same act, and
naming yourself with the nickname you already hold is admitted — and refused with
`NicknameAlreadyTaken` when the handle is another player's. The spec abbreviates the path to
`/me/name`; it sits beside `GET /api/v1/users/me` because the refusal it carries is the users
context's. It records **one event, `UserNamed`** (`users.user_named` / v1), carrying both values;
the fold keeps the latest. The uniqueness read is the one `RegisterUser` made until now, moved to
the act that needs it.

**`GET /api/v1/users/me` carries `name: string | null` and `nickname: string | null`** — null
until the naming, and this is the one read where either may be null.

### 3. The entry gate reads the name before anything else

The gate ([ADR-0090](0090-onboarding-per-player-checkpoint.md); `entryDecision.ts`) gains a
destination and it goes **first**:

> **no name → the naming step** · unfinished run → resume · no ratings → welcome · ratings but no
> Player profile → the social steps · otherwise → the app

**First, because every destination after it says the player's name.** The questionnaire may
address them by it; every surface inside the app does. A run half-answered by an account with no
name cannot be produced by the flow — the naming step precedes welcome — but the gate does not
assume it away, which is the lesson ADR-0090 wrote about its own fourth destination: a shape the
flow cannot produce is still a shape the gate must route, or it loops.

**It passes the glossary's test the way the profile did.** *There is no onboarded player* bans a
per-player flag standing in for a per-sport fact, and asks: *is this really asking whether a
rating exists for this sport?* A name has no sport dimension; *does this player have a name* is
a per-player question with a per-player answer, served as a field on `GET /api/v1/users/me`
rather than as a second round trip, exactly as `has_player_profile` is. It is read from the
`User`'s own stream, not from a projection, for the reason [ADR-0089](0089-player-profile-context-event-sourced.md)
gave for the profile flag — *read models can lag, and the gate's read must come from a source
that is correct immediately after the commit*: the moment after the naming is exactly when a
lagging read would send a player back to a step they just finished.

**The step cannot be skipped.** The hardware back does not leave it
([#451](https://github.com/Rakieta02/Rakieta/issues/451)'s own criterion); it submits the naming,
re-reads `/me`, and only then moves to welcome. A player who closes the app between sign-up and
the naming lands back on it.

### 4. The name is what is said, and the nickname is drawn in two places

**Every read model that names another player carries `name` where it carried `nickname`** — a
challenge's seats (`SeatSchema`, `DetailSeatSchema`, `CourtPersonSchema`), a room's members
(`ConversationMemberSchema`, `ConversationPersonSchema`), a game's seats (`SeatingSchema`), the
candidate rows of the search and the deck (`PlayerCardSchema`), the head-to-head and the yes
screen's people. **The field keeps exactly the nullability the nickname had** — nullable on a
seat that can stand open or outlive its account (ADR-0141 §1's test, *a seat with no name is
still a person who was on the court*; ADR-0162's open seat), required on a card, a court person
and the record — **and a null there never means *unnamed***: a player on any of those surfaces
has necessarily been named, because the gate holds an unnamed account at the naming step. That
guarantee is what the spec's *required there* means, and it is the gate's to keep. **The
record's read carries both** `name` and `nickname` (`PlayerRecordResponse`), for one's own record
and for another player's. This is a **straight rename** on the contract, not an expand-and-
contract. **Contradicts [`docs/environments.md`](../environments.md)'s *renaming a field is all
three phases … never one commit* — on ADR-0164 §1's
precedent and for its reason**: the sequence exists for a released build that stays installed on
real phones, there is none — only `local` runs — and the drift check is what keeps the two apps
honest on the branch, red between the backend ticket and the client ticket that regenerates from
it and green at the end. The rule is not amended: it is right the day a build ships, and from that
day every later rename is two steps.

**The whole name or nobody.** ADR-0107 §4's rule reads on names now: every sentence naming
somebody uses the whole name; nothing invents a first name; the unknown player stays a question
mark. Its three admissions are unchanged and are re-stated here so that nobody re-derives them:

- **The stem** (ADR-0157) keeps its break — *a dot or a space* — and draws `Diego` for `Diego
  Fabregat`, in a box, never in a sentence and never as an accessible name. It is the first time
  the space half of that rule is exercised, and it produces what looks like a first name. **It is
  still not one**: it is a prefix the owner typed, cut at a character the owner typed, which is
  what §4 admitted and what the prototype's `split(' ')[0]` was refused for lacking. What changed
  is that the owner now gets to type a space. That is what a seat label draws — the stem, cut at
  a word and never inside one — and what a box does past it, its own one-line tail ellipsis
  (`the-play-components.md` §5), is that box's business, as §15 already says; it is not reopened
  here.
- **The initials** (ADR-0167 §3) are cut from the name by the same break: *Ania Kowalska* → `AK`,
  *Diego* → `DI`. The four-sided fence stands — never spoken, never in copy, never over a
  photograph, never on any other surface — and the tile's accessible name is the whole name.
- **A seat label may truncate visually; a sentence may not, and a spoken name never does.**

**`@nickname` is drawn under the name on the You tab and on the record screen, and nowhere
else.** Never in a sentence, on a row, a card, a sheet, a toast, a seat label or a spoken name.
Every line that names somebody stays one name long.

### 5. The seed spells names as names

The seed names every account **`First Last`** and gives each a **lowercase handle without a
dot**, unique by construction; the dev roster prints both beside the email. The catalog's *two
surname pools* argument stands — it is about uniqueness by construction, which the nickname still
needs — and its *`First.Last` and not `First Last`* argument is superseded by this record, which
is what it asked for.

## Consequences

- **Every screen changes one word and every read model renames one field.** The drift check is
  red between [#450](https://github.com/Rakieta02/Rakieta/issues/450) and
  [#451](https://github.com/Rakieta02/Rakieta/issues/451), by design; the branch rule is green at
  the end, not per ticket. The formatter that turns a player into words reads `name` and keeps
  its word break; its tests move from handles to names.
- **Two people may share a name, and a row cannot tell them apart.** That is accepted: a row is
  not where two Anias are told apart, the record is, and the record is where the `@nickname` is.
  Anybody who wants the handle on a row has to show a sentence that needs it.
- **An account can exist unnamed.** Sign-up creates one, and the gate holds it at the naming step.
  Every read model that names a player promises that a null there is an open seat or a lost
  account and never an unnamed one, which is a claim the gate keeps true — a surface that reaches
  an unnamed player some other way will draw `?` for a person who exists, and the read is the
  first place it will show.
- **The stem now often is the first name.** `Diego` drawn for *Diego Fabregat* is a truncation and
  is drawn only where a box draws; the docstring has to say that the distinction ADR-0157 argued —
  *this is not a first name* — is now *this is not an invented one*. A reviewer who reads the
  output alone will see a first name, and the rule is what says why that is allowed.
- **The name is free text shown to strangers, and nothing filters it.** ADR-0170 §2's contact
  fence — a phone number, an email, a URL, a handle — is written for the intro and is not applied
  to the name today: a name is two to sixty-four characters, and a rule tuned for a sentence would
  refuse *O'Neil-Ferrer* before it refused anything worth refusing. **Named as a gap, not as a
  decision**: the day a name carries a phone number, the intro's rule is the pattern to reach for,
  and it slots in at the naming.
- **`UserRegistered` changed shape at v1.** No store outlives this branch, so no stream carries
  the old shape and nothing has to upcast; the day a store does outlive one, the version is the
  first thing that has to move for a change like this, and this record is the precedent that says
  why it did not here.
- **A player who signs up and closes the app has an account with nothing on it.** Two moments
  where there was one — credentials, then who you are — and the second can be missed. The gate
  is the whole answer, and it costs a read of `/me` the app already makes.
- **The seed's names are real-looking, and the QA walks read like the product.** Every walk that
  quoted *Diego.Fabregat* now quotes *Diego Fabregat*; the copy spec and the mocks already do.
