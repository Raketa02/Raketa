# ADR-0185 — One account holds several profiles, and a password change signs out everywhere

- **Status:** Accepted — **its §4 amended 2026-11-03 by [ADR-0199](0199-a-player-is-known-by-their-nickname.md)** §3–§4: an account
  an Invitation opens holds no player name, the name the club typed stays on the Administrator, and
  the naming asks for a nickname alone. The gate's first player destination reads *no nickname*.
  Everything else stands.
- **Date:** 2026-09-25
- **Amends [ADR-0004](0004-jwt-access-with-rotating-refresh-tokens.md)** in two places, and
  takes the "new decision" its *Harder* reserved:
  - **Every token names an audience**, and refresh tokens record whose they are (§6).
  - **An access token issued before its account's credentials-changed instant is refused** (§7).
    ADR-0004 wrote that immediate revocation *"is a new decision (a denylist or a much shorter access
    lifetime), not a tweak to this one"*. This is that decision, and it is neither of the two: it is
    one instant per account.
- **Narrows [ADR-0124](0124-the-matcher-gates-account-state-never-age.md) §1.** *Age is an account
  precondition* becomes **a precondition of playing**. An account created by an Invitation isn't
  adult-attested, and *Start playing* asks before anything player-side (§5). Sign-up still refuses
  without an attestation, and no Skill rating can exist without one.
- **Amends [ADR-0171](0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
  §2 and §3.**
  - An account an Invitation created is **not unnamed**: it carries the club-typed Name and no
    Nickname.
  - The naming stays one act, and its step **asks only for what's missing** (§4).
  - The gate's first destination reads *not named in full*: no name, or no nickname.
- **Amends the entry gate of [ADR-0090](0090-onboarding-per-player-checkpoint.md)** (as ADR-0171
  amended it) by one read placed **ahead of all five destinations**: the account's profiles (§3).
- **Amends [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §1's locked header card by one element**: the **profile switcher chip**, which sits in the You
  tab's header in the player profile and in the administrator one alike (§3, club mock 7). 0179's
  own rule applies. The prototype is locked, and where a mock and a record disagree the record is
  amended. Nothing else on the tab moves.
- **Revisits the glossary's *Player* entry.** It said to revisit the model *"if club staff share this
  accounts system"*, and now they do.
- **Grows [ADR-0002](0002-event-sourced-user-aggregate.md)'s `User` stream** by the facts this record
  needs: an attestation given after registration, and a password set, changed or cleared. It stays
  one aggregate.
- Settles [#501](https://github.com/Raketa02/Raketa/issues/501) for the PRD
  [#500](https://github.com/Raketa02/Raketa/issues/500). Built by
  [#503](https://github.com/Raketa02/Raketa/issues/503) (audiences),
  [#507](https://github.com/Raketa02/Raketa/issues/507) (signing out everywhere),
  [#508](https://github.com/Raketa02/Raketa/issues/508) (profiles on `/users/me`, the attestation act),
  [#517](https://github.com/Raketa02/Raketa/issues/517) (Start playing) and
  [#518](https://github.com/Raketa02/Raketa/issues/518) (the switcher and the gate).

## Context

Until now, an account has meant a player. PRD #500 adds a second way to be here, the **Administrator**
([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)),
and many administrators already play. Tomek plays padel, and Ogrody 33 wants him to run its padel
WhatsApp group. Marta runs two clubs' groups and has never played on Raketa.

The forces:

- **One email, one password, whatever the person is.** A second account for the second role would put
  two passwords behind one address. The `users` email is unique, so it couldn't be made anyway.
- **Switching must be instant and passwordless.** Tomek flips between his games and his group's
  requests several times a day.
- **Each club's groups stay that club's.** Marta at Ogrody 33 and Marta at Bonarka Arena are two
  administratorships.
- **Nobody can sign out a lost phone today.** Access tokens are verified statelessly until they expire
  (ADR-0004), and there is no password reset to trigger anything.
- **Club accounts now exist too**
  ([ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §3).
  A club token must never work on the player surface, or a player token on the club surface.

The glossary's *Player* entry anticipated this exactly: *"not a separate aggregate and not a separate
id … Revisit only if … club staff share this accounts system."*

## Decision

### 1. An account holds profiles: acting as a player, and one Administrator per club

A **User** may act **as a player**, which is everything that exists today (the naming, the ratings,
the Player profile), and **as an Administrator** for each club that named them. It may do either or
both, under **one email and one password**. There is no new aggregate. The player side is what the
account already holds, and each administrator side is an Administrator aggregate linked to it.

***Profile*, as the switcher says it, is UI vocabulary.** It names which of those the app is currently
wearing. It is **not a domain term**, because **Player profile** already names an aggregate, and a
second meaning would make every sentence containing *profile* ambiguous.

### 2. `/users/me` says which profiles the account holds

It gains:

- **Whether the account acts as a player.** This is the existing player-profile and ratings state,
  unchanged.
- **The clubs it administers.** One entry per active Administrator.
- **Any pending invitation addressed to its email**, so the app can offer it.

### 3. The entry gate reads the profiles first

Ahead of every onboarding destination:

- **An account with only administrator profiles goes to the administrator area and skips onboarding.**
  It hasn't asked to play.
- **An account with both opens in the profile used last**
  ([ADR-0188](0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)),
  and in **Player** by default.
- **A pending invitation for the account's email shows its sheet on launch.**
- **An account with no profile at all goes to the player setup, starting with the Adult
  attestation** (§5). The only way to get here is an administrator-only account whose club removed
  it ([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md) §7).
  The account stays, and signing in again must never be a dead end. So it takes the same three
  steps as *Start playing* (§4), from the gate instead of from a row.

Past that read, the player side's gate is ADR-0090's as amended by ADR-0171, with its first
destination re-read in §4. **The switcher chip lives in the You tab's header**, in each profile
(club mock 7), and opens a sheet listing the account's profiles with a tick on the current one.
Switching is instant (§6).

### 4. *Start playing* makes an administrator a player, and the naming asks only for what's missing

From the administrator's You tab, **Start playing** leads through three steps:

1. The **Adult attestation**, if the account hasn't given it (§5).
2. **The naming.** An account an Invitation created already has the **Name** the club typed and no
   **Nickname**, so the step shows only the nickname field.
3. **The player setup**: onboarding, as for anybody.

Afterwards the switcher shows both profiles.

**The naming stays one act** (ADR-0171 §2). The request still carries both values. The step sends the
Name the account already holds, and a later change from the You tab is the same act as before. The
gate's first destination becomes ***not named in full***: no Name, or no Nickname. That's the same
destination as before for every account sign-up creates, because such an account has neither until
the naming.

### 5. The Adult attestation is a precondition of playing, not of holding an account

**Sign-up still requires it**, and `RegisterUser` still refuses without it. **An account an Invitation
created doesn't hold one.** Nothing about running a club's groups asks how old anybody is, and the
club typed the email, not the person. The attestation is asked **the first time the account acts as a
player**, before anything player-side can be reached. It's recorded on the `User` stream by an act on
the existing account.

The invariant that matters survives unchanged: **no Skill rating, no Player profile and no place in
any pool exists for an account that hasn't attested**. ADR-0124's *adults only*, and its *attestation,
not verification*, are untouched.

### 6. Every token names its audience

- **Two audiences**: the **player app** and the **club** website.
- A club token is refused on the player surface, and a player-app token on the club surface.
- **A token without an audience is read as a player-app token**, so sessions issued before this record
  survive.
- **Refresh tokens record whose they are**: a `User` or a Club account.

**The administrator profile runs under the player-app audience.** It lives inside the player app, and
switching profiles is **client state, not a new token**. That is what makes switching instant and
passwordless. The administrator's authority isn't in the token at all: every administrator operation
names its club and is checked for an active administratorship on every request
([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md) §7).

### 7. Signing out everywhere is one instant per account

Every account, `User` and Club account alike, gets a **credentials-changed instant**. When it moves:

- **every access token issued before it is refused**
- **all the account's refresh tokens are revoked**

It moves on:

- *Forgot password?*
- the club's *Reset password*
- any other password change

For a `User`, the change is **an event on the `User` stream carrying the new hash**, or none when the
club's reset clears it. It is projected onto the `users` row, whose instant is compared with the
token's issue time. **Every player-surface request already reads that row**, because every `User` a
route is handed is read from it, so the check costs no extra read there. A club request pays the
equivalent read on the club account's row.

The session that the reset itself signs in has to survive its own instant. A comparison that loses to
second-granularity issue times would sign the person out of the session they just opened. The backend
tests both sides of that edge.

## Consequences

**Easier**

- One password, whatever the person does here, and a switch that costs nothing.
- A lost phone loses access the moment its owner resets their password.
- A club credential and a player credential can't be confused, even for the same email.
- The *Player* entry's condition has fired, and the model answers it without a second id.

**Harder**

- **Access tokens are no longer verified statelessly.** On the player surface the row was already
  being read, so the change is free there. On the club surface it's a new read per request. A future
  stateless path, such as a service that verifies tokens without the database, would have to carry
  the instant with it.
- **Tokens without an audience stay accepted** as player-app tokens until every one issued before this
  record has expired. Nothing closes that window except time, and a later record that stops accepting
  them must check that it has.
- **The gate grows.** Profiles, the last profile and the invitation sheet are read ahead of five
  destinations that were already ordered carefully. Every shape the flow can't produce is still a
  shape the gate must route, or it loops. That's the lesson ADR-0090 wrote about its own fourth
  destination.
- **A Name without a Nickname is a new shape.** ADR-0171's guarantee, *"a null there never means
  unnamed"*, holds only because an administrator-only account never appears on a player surface: it
  has no ratings and no Player profile. Anything that ever shows administrators to players has to
  re-check it.
- **The Adult attestation is no longer a sign-up-only fact.** It can be given later, and a reader who
  assumed *every account attested at registration* is now wrong about invitation accounts.
- **The administrator's authority is re-read on every request.** That is what makes removal immediate,
  and it is one more read per administrator operation.
