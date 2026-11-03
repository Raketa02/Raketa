# ADR-0188 — The phone remembers three choices per account, and forgets them at sign-out

- **Status:** Accepted — **its §2 amended 2026-11-03 by
  [ADR-0200](0200-a-level-is-asked-where-play-begins.md) §8**, the new record §5 asks for, with a fourth value: *the guide on Your
  rating was shown*, **per phone rather than per account, and kept at sign-out**. §2's *every value
  is keyed by the account* and §3's *signing out empties the store* hold for the other three. The
  fence still admits this one module.
- **Date:** 2026-09-25
- **Reverses the player app's practice that nothing but credentials and the flag datafile is kept on
  the device**, for **exactly three values**. Nothing else is reversed.
- **Narrows the enforcement of [ADR-0008](0008-player-mobile-securestore-direct-api.md) a second
  time**, not its decision. *`AsyncStorage` must never hold a credential* stands. The lint fence that
  ADR-0180 made *an
  allow-list of one, which a later module can ask to join* admits **a second module**, the
  phone-preferences store, and this is that request. The boundary test keeps asserting the ban
  everywhere else.
- **Doesn't adopt [ADR-0013](0013-player-app-runtime-architecture.md)'s *persistence layer*.** The
  app stays network-backed. This store holds three choices the player made, never a copy of server
  state. **ADR-0013's logout sequence gains a step**: the store is cleared, beside the cache clear
  that sequence already calls a privacy control.
- Settles [#501](https://github.com/Raketa02/Raketa/issues/501) for the PRD
  [#500](https://github.com/Raketa02/Raketa/issues/500). Built by
  [#512](https://github.com/Raketa02/Raketa/issues/512) (the store and the segment),
  [#513](https://github.com/Raketa02/Raketa/issues/513) (the last sport) and
  [#518](https://github.com/Raketa02/Raketa/issues/518) (the last profile).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The flags' datafile cache, the first module this record's allow-list admitted, went with the feature flags (#576), so the allow-list is one module again: the phone-preferences store.

## Context

PRD #500 asks for the app to reopen as the person left it:

- **Play reopens on the segment last used**, Groups or Explore, even after the app is closed (story 4).
- **A group's sport filter opens on the sport last picked anywhere in Play**, even after a restart
  (story 58).
- **Someone with two profiles reopens in the one they used last** (story 138). A coach who
  administers all morning shouldn't land in their player profile every time.
- **All of it per account, and wiped at sign-out**, so nothing leaks to the next person who signs in on
  the phone (story 88).

The app keeps nothing like this today. Tokens live in the keychain (ADR-0008). The flag datafile is
the one thing in `AsyncStorage` (ADR-0180), and the lint bans `AsyncStorage` everywhere else. Every
other value lives in memory and dies with the process.

Rejected on the way:

- **Preferences on the server.** Play would need a round trip before it could choose a segment. It
  would also cost a write on every tap of a switch, and it would make one phone's habit follow the
  account to another phone, which is not what was asked.
- **Memory only.** That loses the choice at every restart, which is the one thing being asked for.
- **The keychain.** It's the credentials store, and one module owning it is what makes token lifetime
  auditable (ADR-0008). Filling it with preferences blurs exactly that audit.

## Decision

### 1. One module, the phone-preferences store, is the only other importer of `AsyncStorage`

The lint fence admits exactly this module, beside the flag datafile cache. Nothing else in `src/`
may import `AsyncStorage`, and the boundary test asserts both halves. #512 places the module.

### 2. It holds three values, per account

| Value | What it is | Default |
| --- | --- | --- |
| **Play segment** | Groups or Explore | Groups |
| **Last sport** | the sport last picked in any group's fast filter, anywhere in Play | the first sport the player is rated in, in the order padel › tennis › squash › badminton |
| **Last profile** | Player, or the Administrator profile for one club | Player |

**Every value is keyed by the account**, so a second account signed in on the same phone never
inherits the first one's choices.

### 3. It's cleared at sign-out

Signing out empties the store, as a step of the logout sequence (ADR-0013). Being signed out by the
server counts: a password reset elsewhere, or a removed administrator with no player profile. So does
signing out by hand.

### 4. A stale or unreadable value is its default, never an error

Each read is checked against what the app knows:

- **A sport** the player is no longer rated in falls back to the default.
- **An administrator profile** the account no longer holds falls back to Player.
- **A store that can't be read**, or a value it doesn't recognise, gives the defaults.

The store is **local and never waits on the network**. It is read before the first screen that uses
it, so no screen draws one choice and then jumps to another.

### 5. What isn't remembered

- **The Competitive / For fun switch** on the Friends tab keeps its position while the app is open, in
  memory only.
- **Search text**, **which tab a group page was on**, and **anything the server knows** aren't kept.
  A group page always opens on Games.

Adding a fourth value is a new record, not an edit to this one's table.

## Consequences

**Easier**

- The app reopens where the person left it, on every restart, without a round trip.
- The next person on a shared phone starts clean.
- The fence still says exactly which modules may touch device storage, and why.

**Harder**

- **The allow-list is now two, and the argument for the third is now easy to make.** Every future
  request to remember something on the phone will cite this record. The table in §2 is the limit, and
  holding it is a review discipline, not a lint rule.
- **Every value can go stale while the app is closed**: a rating withdrawn, an administratorship
  removed. §4's checks on read are the only defence, and a new value added without its check will
  restore a choice that no longer exists.
- **A read before the first screen is a read on the launch path.** It's a local key–value read and
  cheap, but it is one more thing between the splash and Play, on the path ADR-0013 spent care on.
- **Clearing at sign-out means a person who signs out and back in loses their choices.** That's
  intended, because the store can't tell *me again* from *somebody else*.
