# ADR-0182 — A club is a place players search, and its account signs in only on the club surface

- **Status:** Accepted
- **Date:** 2026-09-25
- **§8's *a club isn't a court* superseded 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**: a club lists courts, hours and prices and sells them through Rakieta in one of three ways of working. A plan's *where* in the Classic play loop is unchanged.
- **Answers [ADR-0002](0002-event-sourced-user-aggregate.md)'s per-context question for Clubs:**
  *event-sourced*, with a synchronous search projection.
- **Narrows ADR-0144's** *"there
  is no club record to hold the true one"* and its *"the price of refusing a venue record"*. A club
  record now exists. **A plan's *where* is unchanged**: it stays free text that nothing reads, and
  the one platform zone stays. The club record doesn't become a plan's venue (§8).
- **Narrows [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)'s *No tenant data*.**
  That section said clubs are *"owned by their contexts"*, and until now no such context existed.
  The Club context now owns them. The kernel still holds none, and `Sport` stays the closed
  registry that a club's sports filter.
- **Keeps clubs out of the glossary's *Player* model.** That entry said to revisit it *"if club staff
  share this accounts system"*, and
  [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  does, for Administrators. A club isn't staff and isn't a person. A Club account is **not** a
  `User`, and is never matched, rated or shown to a player.
- Settles [#501](https://github.com/Rakieta02/Rakieta/issues/501) for the PRD
  [#500](https://github.com/Rakieta02/Rakieta/issues/500), grilled 2026-09-24/25. Built by
  [#503](https://github.com/Rakieta02/Rakieta/issues/503) (backend) and the club website's tickets
  [#522](https://github.com/Rakieta02/Rakieta/issues/522)–[#524](https://github.com/Rakieta02/Rakieta/issues/524).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** Plans went with Classic play, so §8's *it isn't a plan's venue*, the header's narrowing of ADR-0144 and the last *Harder* bullet describe nothing that exists; §8's first half was already superseded by ADR-0189. A game's place is a club's court, named on the card that proposes it. Everything else stands.

## Context

**The platform has no concept of a club.** There is no club record, no venue and no district. A
plan's *where* is free text, and ADR-0144 refused a venue record in writing, because nothing in
the build could own one. The 2026-08-25 reset removed a club console and the Clubs context that
was planned under it. The glossary has had no club vocabulary since.

PRD #500 needs one, for three reasons:

- **A group has a home club, and it's required** ([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)).
  A player creating a group searches every club in Rakieta by name or district, nearest first. A
  player joining one searches the same clubs and sees their groups inside them.
- **A club signs up on its own website**, invites the people who run its WhatsApp groups
  ([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)),
  and watches its official groups fill. The desk shares one login.
- **The desk can change the club's details at any time.** A mistake made at sign-up must not
  stay for ever.

Two identities are in play, and they must stay apart. A club isn't a person. The person at the
desk may also play, under their own email, and the club's email may even belong to someone's
player account. A club must never be able to act on the player app, and a player must never be
able to act on the club website.

Rejected on the way:

- **A club as a `User` with a new `Authority`.** It would make the club's credential a player
  account, reachable on the player surface, and it would collide with the `ADMIN` authority
  that already means something else. It would also force the email to be unique across clubs and
  players, which is false: a café owner's personal address can also be the club's.
- **Clubs as catalog rows loaded by an admin.** Rakieta would then have to know every club before
  the club did. That contradicts *a club exists because it signed up*, and it leaves no history of
  who changed what.
- **The club's credentials on the club's own stream.** It's simpler, and it puts a password hash
  on the stream that the search projection is built from. A club's facts are public: they're
  searched by every player and published on every group page. Its credentials aren't. A password
  change also belongs to the account, not to the place.

## Decision

### 1. A Club is an event-sourced aggregate

A **Club** holds a name, a district, a city, **the sports it offers** (a non-empty subset of the
four `Sport` values), and **a precise location point**. Its stream starts with *registered*, and
every later edit is *details changed*. It uses the repository machinery every other aggregate
here uses ([ADR-0018](0018-aggregate-repositories-over-the-event-store.md)).

The club's sports **filter** the registry and never extend it. A club can't declare a fifth sport
or change a sport's player count; the kernel's invariant holds structurally.

### 2. Search reads a synchronous projection, never the stream

A **search projection** is written **in the same transaction** as the event, the way `users` is.
It holds the club's facts plus **folded** copies of the name and the district. Home-club search
and join search ([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §9)
read it and nothing else. A club edit is visible to the next search, never "eventually".

**Folding is lower case with accents stripped, and matching is "anywhere in the field".** Typing
*debniki* finds *Dębniki*. Polish needs one explicit mapping: **ł → l**. Unicode decomposition
strips the ogonek from *ę* but has nothing to strip from *ł*, which is its own letter, so a fold
built only on decomposition would never find *Błonia*. The query and the stored copies are folded
by **the same function**, so the two can't disagree.

### 3. The club account is a separate identity, and it signs in only on the club surface

A **Club account** is the club's sign-in: one email and one password, created **together with the
club** and shared by the desk. It is **its own event-sourced aggregate**, never folded into the
Club, for the reasons given under *Rejected on the way*.

- Its email is **unique among club accounts** and may also belong to an unrelated `User`. The two
  are different identities with different passwords, and nothing links them.
- Its password follows **the same rule and the same hashing** as a player's (`RawPassword`,
  `HashedPassword`). A second rule would be a second thing to get wrong.
- It signs in **only on the club surface**. Its tokens carry the club audience and are refused on
  the player surface, and a player's are refused on the club surface
  ([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §6).
- It has its own **Forgot password** and its own **credentials-changed instant**
  ([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md) §5,
  [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §7).

**One account per club.** Several desk logins per club is a later decision. The account having its
own identity is what leaves room for it.

### 4. Signing up creates the club and its account together

One request, one transaction: name, district, city, sports, map pin, email and password. **There is
no verification step and no per-club URL.** Every club signs in at the same address, and the
session says which club it is.

### 5. The details can change at any time, with one refusal

The desk may change the name, district, city, sports and pin whenever it likes. **Removing a sport
that an official group declares is refused, and the refusal names the group.** Otherwise a group
would be left playing a sport its club no longer offers
([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §3). A rename
changes nothing about any group: a group's link never contains its club's name.

### 6. The location is a precise point, because a club is a public place

A player's **Location area** is coarsened to a cell about a kilometre across, because where a
person plays is a fact about the person. A club's point isn't: it's printed on the club's door.
So **the club's point is stored as the desk dropped it**.

The distance shown to a player is measured from **the caller's Location area** to the club's point
and printed by **`shown_kilometres`**: one decimal, never below a tenth, the rule the radar and the
shortlist already print by. A caller with no Location area gets **A–Z and no distances**, because
nothing should pretend to know where they are.

### 7. Nothing about clubs is hard-coded

A club exists because a club signed up, or because the seed made it **through the same use cases**
([ADR-0029](0029-seed-data-through-aggregates-never-in-production.md)). The seed makes about eight
Kraków clubs, placed relative to the seed centre, each with a club account on the seed password.
No application code names a club.

### 8. A club isn't a court, and it isn't a plan's venue

The copy says *"a court at [club] is free"*. That sentence talks about physical courts. **There is
still no court record, no booking, no inventory and no price**, and ADR-0145's refusal list stands
whole.

**A plan's *where* stays free text that nothing reads** (ADR-0144). The obvious next request, *pick
the club in the plan*, becomes answerable now that clubs exist, and this record doesn't answer it.
Linking a plan to a club would make the platform assert where people are meeting. It would also
reopen the one platform zone, since a club record carries no time zone. That is a decision with its
own cost, and it gets its own record.

## Consequences

**Easier**

- A group can require a home club, and search has one table to read, in one transaction's
  freshness.
- The desk owns its own facts and fixes its own mistakes. Nobody at Rakieta is on the path.
- The kernel stays free of tenant data. The club data now has a context that owns it.
- The club account and the `User` never meet. A bug in one sign-in can't hand anyone the other.

**Harder**

- **Nobody checks that a club is who it says it is.** Anyone can sign up as *Ogrody 33*, twice,
  and players may pick the impostor as their home club. Recorded as out of scope. It is reopened
  the first time a club holds something worth stealing, such as courts, bookings or money.
- **One email can hold two unrelated identities with two passwords.** A desk worker who plays gets
  two *Forgot password?* forms for one address, one on the website and one in the app, and support
  has to ask which one they mean.
- **The folded copies are a second spelling stored beside the first.** Changing the fold rule means
  re-projecting every club, and a fold that misses a letter (the *ł* case) fails silently as "no
  club called …".
- **"Anywhere in the field" is a scan.** It's free at eight clubs and slow at eight thousand. A
  trigram index is the known next step, and nothing here stops it.
- **A club's precise point is published to every player.** That's intended, since a club is a
  public place, but it means the pin is the club's responsibility. A desk that drops it on a home
  address publishes a home address.
- **The plan's *where* is still free text even though clubs exist.** A player will ask why the club
  they chose for their group isn't offered when they write down where the game is. §8 is the
  answer, and it will need repeating.
