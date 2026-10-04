# ADR-0192 — A handover is told to whom it was handed, and the app follows the account

- **Status:** Accepted
- **Date:** 2026-10-04
- **Amends [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §8.**
  *"One event, administrator assigned, records it"* gains a second event: **`handover_seen`**, once
  the new Administrator has been told (§1). The handover itself is unchanged.
- **Adds to [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §2's account read.** `/users/me` `profiles` gains **`handovers`** beside `pending_invitations`
  (§1).
- **Leaves [ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
  §7's** *"Removal needs no push and no revocation list"* intact. The app now re-reads the
  account on a timer while an administrator has it open (§3). That is a poll, not a push, and it
  makes a removal arrive sooner as a side effect.
- Decided at the #529 QA walk of PRD [#500](https://github.com/Raketa02/Raketa/issues/500)
  (N5–N7), at the product owner's ask: *"whenever a handover is done the bottom dialog should
  appear to inform"*. They asked for two evaluations: which buttons the sheet carries, and whether
  it must appear without the app going to the background.
- Numbered after [ADR-0191](0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md),
  from the same walk. 0190 is on `feature/games_fillin_club`.

## Context

**A handover reached nobody.** The club gives an official group to an active Administrator
(ADR-0183 §8), and the group appeared in that person's Groups tab on its next read. Nothing said
so. The person usually inherits a queue (*"the waiting ones included"*), so the people waiting
stayed waiting until the new Administrator happened to open the tab and notice a card they
didn't create.

**The invitation sheet is the model the product owner pointed at.** A club naming someone is told
to them in the app, on a sheet over whichever profile they are in (#518). That sheet reads
`/users/me`, which the app re-reads only when it comes back to the foreground. So anything new
appeared only after a background-and-return or a relaunch. The QA walk is full of *"wait 30
seconds, press Home, open Raketa again"* for exactly that reason.

Considered and rejected:

- **Remembering *told* on the phone.** ADR-0188 fences the phone's storage to three choices. A
  phone-side flag would tell the person once per phone, and again after a reinstall. Told is a
  fact about the person, so the server keeps it.
- **A table of notices outside the event store.** The group's stream already records the handover.
  Whether its new Administrator has been told is the second half of that same act, and putting it
  on the stream keeps *state changes emit events* without an argued exemption.
- **Instant delivery.** There is no channel that can wake the app. Push notifications are gated off
  on the games branch, and the live channel is one room's (ADR-0147). Building a user-level stream
  for one sheet is out of proportion.
- **Re-reading every signed-in account on a timer.** Most accounts administer nothing, and their
  only incoming fact (an invitation) can wait for the next foreground, as it does today.

## Decision

### 1. *Told* is an event on the group, and the account's read lists what is untold

- **`AdministratorAssigned`** now also sets the group's `handed_over_at`: when it was handed to
  whoever runs it now.
- **`HandoverSeen`** (`groups.handover_seen` v1: `group_id`, `administrator_id`, `seen_by`,
  `occurred_at`) clears it. It is recorded **only by the administratorship that runs the group**,
  and **only while something is untold**. A group its Administrator created was handed to nobody.
- **Handing the group on** before the first person was told makes it the next person's to be told.
  Handing it back to someone makes it theirs again.
- **The projection** gains `groups.handed_over_at` (nullable; migration `0035_handover_notices`).
- **`/users/me` `profiles.handovers`** lists, oldest first, every untold group handed to the
  account's **active** administratorships: `club_id`, `club_name`, `group_id`, `group_name` and
  `waiting_count`. A removed administratorship is told nothing. Administrators reads it through
  `OfficialGroupAssignments.handed_untold`, the port groups already answers for it.
- **`POST /api/v1/administrator/clubs/{club_id}/handovers/seen`** takes `{group_ids}` (1–100),
  passes the administrator guard (`403 not_an_administrator`), and returns `204`.
  - Anything it can't apply is **stepped over, never refused**: a group handed on meanwhile, one
    already told, one that isn't theirs.
  - The person closed a sheet, and a stale sheet is not their mistake to be refused for.
  - This also makes the route safe to send again, so it is the one administrator write the app
    retries.

### 2. The sheet: where to go, or nowhere

The evaluation of the buttons: **nothing is asked, so nothing can be declined**, and *only
dismiss* would throw away the one thing the person most likely wants next, which is the queue.

- **One club at a time, with every group that club handed.** A club that hands over three groups
  at once (the usual case after a removal) is one sheet, not three. The club of the oldest untold
  handover goes first.
- **The heading** is the club's tile over *"Ogrody 33 made you the administrator of Ogrody 33
  Club"* (*"… of 2 groups"* for several, their names in the body). The body says what running it
  means now, then the queue: *"2 people are waiting for your answer."*
- **Open the group** (one group) goes to its page, where the queue waits. **See your groups**
  (several) goes to the Groups tab. Either switches to that club's administrator profile first if
  the person is wearing another, which is the switcher's move, so the phone keeps it.
- **Got it** and the close (named **Dismiss**, so two controls aren't one name twice) leave the
  person where they are.
- **Every way out records it as seen.** A sheet that came back after *Got it* would be asking a
  question it never put. The groups leave the cached account at once. A write that never lands
  leaves them closed for this launch (in memory) and told again on the next, which is the honest
  answer.
- **It is mounted where the invitation sheet is**: over the player's app and over every
  administrator area. **It waits while an invitation is on offer**, because that sheet asks for a
  decision and this one only tells.
- **The club website's *Hand over* question says so**: *"Raketa tells [name] in the app."*

### 3. The app follows the account while it administers a club

The evaluation of *right away*: **yes, without the app going to the background, within half a
minute.** It is not instant, because there is no channel that could make it instant (see Context).

**While the account administers at least one club and the app is in the foreground, `/users/me`
is re-read every 30 seconds.** That is the query's own staleness window. Query pauses the interval
in the background through the focus manager the app wires to `AppState`. It's an extra observer
of the one query, so nothing is fetched twice.

The same read carries invitations and removals, so for an administrator those arrive within the
same half minute too.

## Consequences

**Easier**

- **A handover reaches the person**, with the queue it brings, on whatever screen they are on.
  The people waiting get an answer sooner.
- **Told is one fact for every phone**, recorded where the handover is. A second phone or a
  reinstall doesn't tell again.
- An administrator's app catches up with the club **without being sent away and back**, which
  takes the *"wait 30 seconds, press Home"* steps out of the QA walk for administrators.

**Harder**

- **A request every 30 seconds per open administrator app.** `/users/me` reads the account, its
  administratorships, its invitations and now one group list per administratorship. That is fine
  at this scale, but it scales with open administrator apps, and it's the first background poll
  the app runs for its whole foreground life. The figure is one constant
  (`ACCOUNT_FOLLOWED_MS`).
- **Not instant, and not delivered to a closed app.** Someone who never opens the app hears
  nothing. The club's ADR-0191 removal email has no handover twin. A push channel would change
  this, and none exists on this branch.
- **A migration on a branch whose sibling chains its own.** `feature/games_fillin_club` has
  `0035`–`0044` on `0034`. Whichever branch lands second re-points its first migration onto the
  other's head.
- **The event stream records a UI moment.** *The sheet was closed* is now a group event. It's a
  fact about the handover being complete, but a future reader must not take `handover_seen` to
  mean the person *read* anything, only that a sheet naming the group was dismissed or followed.
