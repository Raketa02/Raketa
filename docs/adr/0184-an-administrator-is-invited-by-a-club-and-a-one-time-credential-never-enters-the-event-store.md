# ADR-0184 — An administrator is invited by a club, and a one-time credential never enters the event store

- **Status:** Accepted
- **Date:** 2026-09-25
- **§8 narrowed and §7 amended 2026-10-04 by [ADR-0191](0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md)**: the club answers its Official
  groups' Join requests too, and **a removal is emailed to the person**: *removed*, or *invitation
  withdrawn* for somebody who never took it up.
- **Answers [ADR-0002](0002-event-sourced-user-aggregate.md)'s per-context question for
  Administrators:** *event-sourced*. The one-time credentials are deliberately **not** event-sourced
  (§3).
- **Is why [ADR-0186](0186-email-goes-through-a-port-and-a-purged-queue.md) narrows
  [ADR-0003](0003-transactional-outbox-for-event-delivery.md).** An email carrying a secret can't
  travel through the outbox, because the outbox carries domain events and a domain event may never
  carry a secret (§4).
- **Reuses [ADR-0004](0004-jwt-access-with-rotating-refresh-tokens.md)'s** storage rule for a
  secret the server must recognise: only its hash is kept.
- **Shares a name with the `ADMIN` `Authority` and nothing else.** The collision is recorded in the
  glossary. An Administrator holds no platform power and no power over anybody's account.
- Settles [#501](https://github.com/Rakieta02/Rakieta/issues/501) for the PRD
  [#500](https://github.com/Rakieta02/Rakieta/issues/500). Built by the backend tickets
  [#507](https://github.com/Rakieta02/Rakieta/issues/507) (credentials, sign-out everywhere, Forgot
  password), [#508](https://github.com/Rakieta02/Rakieta/issues/508) (administrators and invitations),
  [#509](https://github.com/Rakieta02/Rakieta/issues/509) and [#510](https://github.com/Rakieta02/Rakieta/issues/510),
  the player app's [#515](https://github.com/Rakieta02/Rakieta/issues/515)–[#518](https://github.com/Rakieta02/Rakieta/issues/518),
  and the club website's [#522](https://github.com/Rakieta02/Rakieta/issues/522) and
  [#523](https://github.com/Rakieta02/Rakieta/issues/523).

## Context

Each club has someone who runs its WhatsApp groups: a coach, a desk worker, a regular with a
business tie to the club. For clubs to cooperate, Rakieta has to keep that figure. PRD #500 calls
them the **Administrator**. Their one job is to create an **official group** for each WhatsApp
group and post its link there
([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)).

The forces:

- **The club names the person and must never hold their credentials.** The desk types a name and an
  email and nothing else. It never sets, sees or handles a password or a code.
- **The person may be new to Rakieta or may already play.** A new person needs an account. An
  existing player needs no second password, because one email means one account
  ([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)).
- **The link might not reach the app.** The email may be opened on a laptop, or before the app is
  installed. There is no reliable first-party way on iOS to carry a link through an install, so the
  honest bridge is a **code** the person types.
- **Nobody can recover a password today.** The same machinery serves three flows: the invitation,
  the club's reset of an administrator, and everyone's *Forgot password?*.
- **One person may administer for two clubs**, and each club's groups must stay that club's.

## Decision

### 1. An Administrator is an event-sourced aggregate, one per (club, email)

An **Administrator** is a person acting for one club. There is exactly one per **(club, email)**. It
is keyed by email rather than by account, because the club types an email and the account may not
exist yet. A person administering for two clubs is two Administrators.

Its states are:

- ***invited***: shown as ***expired*** once its credential lapses. Expiry is **derived** from the
  credential's deadline and never recorded as an event.
- ***active***: linked to an account.
- ***removed***: re-inviting after a removal is allowed, on the same stream.

A projection records **when the administrator profile was last used**, updated **at most once an
hour**. The club website's *active · this week* reads it. Updating it on every request would add a
write to every read.

The club website's statuses are all derived: *active · this week*, *invited · expires in 3 d*,
*expired · 2 d ago*.

### 2. An Invitation is how the club names a person, and it has two doors

The club invites by **name and email**. It's refused on the spot if that email is already *invited*
or *active* at this club.

- **A new person** gets an email with a button to the public site's `/invite/<token>` and an
  8-character code under it. They set a password through the link (in the app, or on the public
  page) or through **email + code** on the app's *Have an invitation code?*. That **creates the
  account**, with the club-typed name as its Name, no nickname and no adult attestation
  ([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §4–§5).
  It activates the Administrator and signs them in.
- **An existing account** gets *"[Club] wants to make you an administrator"*, with no password
  involved. The app shows the invitation as a sheet to the signed-in account **whose email matches**.
  **Accept** adds the profile. **Not now** hides it until the next launch, and it comes back until
  it's accepted or it expires. If the code is typed for an email that already has an account, the
  answer is *sign in to accept*.

**Resend** is available while *invited* or *expired*, and gives a fresh 72 hours.

### 3. One-time credentials are one mechanism with three uses

| Use | Lifetime |
| --- | --- |
| Invitation | 72 h |
| The club's *Reset password* of an administrator | 72 h |
| *Forgot password?*, for players, administrators and clubs | 1 h |

Every credential is **a link token plus an 8-character code** from an alphabet with no look-alike
characters, issued together.

- **Both are stored hashed.** The server only ever needs to recognise them, never to show them.
- **Usable once.** Using either one burns both.
- **They expire.** An expired credential says *ask the club to send a new one* (or *ask again*, for a
  forgotten password). A used one never reopens.
- **Five wrong codes lock the credential.**
- **Claiming by email + code returns a short-lived ticket**, and the password is set with the ticket.
  Guessing is bounded to one place.

**They live in a plain table, not in events.** A credential is a secret with a lifetime, while an
event is kept for ever and replayed. An 8-character code's hash kept for ever is a code that can be
cracked offline for ever, because the online lock no longer protects it once the hash is copied. A
table row expires, and it can be purged.

### 4. Secrets never enter the event store

**No token, code or ticket is ever written to the event store or to the event delivery queue.**
Events record *that* an invitation was issued, resent, accepted or claimed, never *what* opens it.

An email carrying a secret is **rendered into a mail queue row in the same transaction** as the act
that issued the secret. A worker sends it and then **purges the secret body**
([ADR-0186](0186-email-goes-through-a-port-and-a-purged-queue.md)). **A use case never sends email
itself.** A test asserts that no token or code appears in the event store or the delivery queue.

**A password hash isn't what this rule is about.** `UserRegistered` has carried one since ADR-0002,
and a changed password is a new event on the same stream carrying the new hash
([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §7).
The difference is who chose the secret and how long it lives. A password is chosen by its holder and
lives as long as the account. A one-time credential is minted by the platform and must die at the end
of its lifetime.

### 5. *Forgot password?* answers the same whoever asks

In the app it serves players and administrators, and on the club website it serves clubs. The answer
to a request is **identical whether or not the email has an account**, so nobody can use the form to
find out who uses Rakieta. Requests are **throttled per email**. Setting a new password follows the
existing password rule, **signs out everywhere**
([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §7),
and signs this session in. A club's reset link points at the club website's own *Set a new password*
page, and a player's or administrator's at the public site's.

### 6. The club's *Reset password* is refused unless the account holds only administrator profiles

For an account that is **nothing but administrator profiles**, the club may reset the password. That
clears it, signs out everywhere, and puts the person back to *invited* with a fresh 72-hour email.
The email carries the invitation's own link and code, and the person sets a new password on the
invitation's page ([ADR-0186](0186-email-goes-through-a-port-and-a-purged-queue.md) §3).
**For any account that also plays, it's refused.**

The argument is ownership. A club that could reset Tomek's password would hand whoever reads the email
Tomek's personal player account: his games, his chats and his record. The club made the
administrator-only account and may help recover it. It didn't make the player account and may never
touch it. A person who both plays and administers recovers through *Forgot password?*, like anybody
else.

### 7. Removal ends the administratorship on the next request

The club may remove an Administrator, after a confirmation.

- The Administrator becomes ***removed***. Their groups stay, marked ***needs an administrator***,
  until a handover ([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §8).
- **Every administrator operation checks for an active administratorship for that club on every
  request.** Removal therefore takes effect on the next request, which gets **a distinct error code**.
  The app turns that code into a message and a move to the player profile, or a sign-out if there is
  no player profile.
- **Their player profile and player sessions are untouched.**
- **An administrator-only account stays** after removal. Signing in again leads into the player
  setup, starting with the Adult attestation, rather than to a dead end
  ([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §3).

### 8. What an Administrator may do

An Administrator creates official groups for their club, answers their join requests, and edits their
settings: name, join policy, WhatsApp group size and declared sports. **They can't delete an official
group, and they can't stop running one.** Only the club moves a group (a handover) or ends the
administratorship. Acting as a player, they join their own groups directly
([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §7).

## Consequences

**Easier**

- One credential mechanism serves three flows, with one set of tests for expiry, single use and
  locking.
- The club never touches a credential, and no secret outlives its email.
- A person who both plays and administers keeps one password, and nobody but them can reset it.
- Removal needs no push and no revocation list. The next request finds out.

**Harder**

- **A mail queue row holds a live secret until the worker sends it.** A database dump taken in that
  window carries it. The window is bounded by the worker's cadence and closed by the purge, and the
  purge has to actually run. A test asserts it, and nothing in production would notice if it stopped.
- **An 8-character code can be guessed in principle.** Five attempts per credential and a short
  lifetime bound any single guesser. Nothing yet stops someone spreading guesses across many
  credentials, because there is no per-client limit. That belongs to the deployed environment's rate
  limiting, which doesn't exist yet.
- **The identity key is an email the club typed.** A typo invites nobody. The club notices only
  because the row stays *invited*, then invites the corrected address, and the wrong one expires.
- **Every administrator request pays one extra read** for the active-administratorship check.
- ***Active · this week* has hour granularity**, and says nothing finer.
- **An account created by invitation is a new shape**: a Name, no nickname, no attestation. The entry
  gate has never had to route it ([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)).
- **The club can't help a member of staff who also plays.** That is intended. The support answer is
  *Forgot password?*, and it will be asked.
