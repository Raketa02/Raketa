# ADR-0183 — A group is a crowd at a home club, and its link never changes

- **Status:** Accepted
- **Date:** 2026-09-25
- **§7–§8 narrowed 2026-10-04 by [ADR-0191](0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md)**: an Official group's **club answers its
  Join requests too, at any time**, beside whoever runs it, and edits nothing in it; a Handover moves
  which Administrator answers.
- **§8 amended 2026-10-04 by [ADR-0192](0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)**: a handover is **told to whom it was handed**, once
  (`handover_seen` on the group), on a sheet in the app.
- **§13 superseded 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**, except *no friends list* and *no removing members*, which stand: a group picks games, members post them, courts are booked, money is handled, and each game has a chat. **§11's *Games* amended by the same record**: it counts the games actually booked in each official group.
- **Answers [ADR-0002](0002-event-sourced-user-aggregate.md)'s per-context question for Groups:**
  *event-sourced*, with synchronous projections for groups, group members and join requests.
- **Amends [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §1's** *"Play
  opens on Find a game"*. Play opens on a **Groups | Explore** switch, and Find a game stays behind
  its flag (§12). §1's other rulings stand: the deck lives on Players, *Match me* is gone, and
  there are still five tabs.
- **Amends [ADR-0180](0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
  §6's** *"`find_a_game` defaults to enabled"*. It now defaults to **off**, both in code and in
  every environment's definition in the flags repo. **§5 stands and is confirmed**: the backend
  evaluates no flag, so neither Find a
  game's endpoints nor the new group endpoints are guarded by one.
- **Reads [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s**
  symmetric effect into a new surface, the Members list (§10).
- **§10's Members list is also read by whoever runs an official group now**, by
  [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)'s
  amendment of 2026-10-02 ([#566](https://github.com/Raketa02/Raketa/issues/566)), which opens
  the record of anybody on it too. Running a group is still not membership (§7): that account is
  no row until it joins as a player, counts in nothing, and a block either way round hides a row
  from it as from a member.
- **Distinguishes [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)'s** *no
  presentation* rule. A monogram's letters are content cut from content, and its colour crosses
  as a key (§5).
- **Distinguishes [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
  §3's** client-cut initials. A group's monogram is served by the backend (§5), and a player's
  initials are still cut by the one client that draws them.
- Settles [#501](https://github.com/Raketa02/Raketa/issues/501) for the PRD
  [#500](https://github.com/Raketa02/Raketa/issues/500). Built by the backend tickets
  [#504](https://github.com/Raketa02/Raketa/issues/504)–[#506](https://github.com/Raketa02/Raketa/issues/506),
  [#509](https://github.com/Raketa02/Raketa/issues/509) and [#510](https://github.com/Raketa02/Raketa/issues/510),
  and by the player app's [#512](https://github.com/Raketa02/Raketa/issues/512)–[#514](https://github.com/Raketa02/Raketa/issues/514),
  [#516](https://github.com/Raketa02/Raketa/issues/516) and [#519](https://github.com/Raketa02/Raketa/issues/519).

## Context

**Racket players in a city already organise, and they don't do it here.** Each club has WhatsApp
groups, usually one per sport, run by someone with a business tie to the club. In them players
arrange a game, one person books the court, and that person chases the others for money. Find a
game is one person searching the whole pool alone. Raketa has no concept of a crowd of people who
already play together.

PRD #500 brings those crowds in without making the club feel it's losing its players. Two shapes of
crowd appear:

- **A player's own group.** It's named freely, set at a home club, and run by whoever made it.
- **A club's official group**, one per WhatsApp group. It's created by the person who runs that
  WhatsApp group, the **Administrator**
  ([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)),
  and its link is posted into the chat so the crowd can follow.

Both need a link that works in WhatsApp, a way in (at once, or by asking), a page, a Members list
and a way out. Neither picks games yet. The Games, Fill in and Friends tabs show a group that is
just starting, and only Info works fully.

Rejected on the way:

- **Two aggregates, one per kind.** They share the link, the membership, the join policy and its
  requests, both searches and the whole page. They differ in three places: who runs them, where the
  sports come from, and whether the runner can delete or leave. Two aggregates would mean two copies
  of every shared rule, drifting apart.
- **The group as a conversation.** A group has no messages, and a Conversation is bound to one
  episode and ends with it ([ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md),
  [ADR-0153](0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)).
  Borrowing it would inherit its end.
- **A link that encodes the group's name, or can be regenerated.** Every WhatsApp post of the old
  link would die on a rename or a regeneration. The club would then have to post again into chats
  it doesn't control.

## Decision

### 1. A Group is one event-sourced aggregate with two kinds

A **Group** is a **Player group** or an **Official group**. Its events cover:

- created
- joined
- join requested, approved and declined
- left
- ownership passed
- renamed
- join policy changed
- sports declared (official groups only)
- WhatsApp size set (official groups only)
- administrator assigned (a handover)
- deleted

Synchronous projections for **groups**, **group members** and **join requests** are written in the
same transaction, the way `users` is. Every rule that differs by kind says so in its own words;
none is left to infer from a null.

### 2. A player group has an Owner, a home club, a name and a join policy

- **The Owner** is the player who created it, until ownership passes (§7).
- **The home club** is required, chosen from every club in Raketa, and **never changes**. Editing it
  is out of scope.
- **The name** is 1–40 characters, trimmed, and not unique. Two groups at one club may share a name.
  The New group form tints a club that already has groups and lists them, so a player can join the
  existing crowd instead of splitting it.
- **The join policy** is *Anyone* (the default) or *People I approve*.

### 3. An official group belongs to a club, has no Owner, and declares what the WhatsApp group is

- **Its home club is its club**, fixed at creation.
- **It has no Owner.** One **Administrator** of that club runs it, or none while it **needs an
  administrator**. With no administrator it reads *"[club] approves joins"*, and its requests wait
  until a handover (§8).
- **It declares its sports**: a non-empty subset of the club's sports, required at creation and
  editable. The club can't untick a sport that a group declares
  ([ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §5).
- **It records its WhatsApp group size**: a whole number from 2 to 1024, required at creation. It's
  the denominator of the club's *From WhatsApp* figure, and it limits nothing. A group may pass 100%,
  and the club sees the real figure (*52 of 48 · 108%*).

### 4. The group link is the public site's address, `/join/`, and a code that never changes

A group's **code** is 8 random characters from an alphabet with **no look-alike characters**. It is
unique and **never changes**: not on rename, not on a policy change, not on a handover. The **Group
link** is the configured public site address followed by `/join/<code>`
([ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §7).

**Any text containing `/join/<code>` is recognised.** That covers a WhatsApp message with words
around the link, a link copied with its scheme or without it, and a link printed under one
environment's domain and pasted into another's. The domain is the setting's business, and the code
is the group's identity.

The mocks' `rakieta.app/g/g4_394` is illustrative only. The shape is this section's.

### 5. The monogram and its colour are served by the backend

- **Letters**: the first character of each of the first two words, **as typed**, or the first two
  characters of a one-word name. *my raketa group* gives `mr`, and *Ogrody 33 Club* gives `O3`.
- **Colour**: a **key**, derived stably from the group's id, that never changes, even on rename.

**Three clients draw this tile**: the player app, the club website and the public site. A rule
written three times drifts three ways, whether the drift is in a digit, an emoji, a leading space
or a one-letter word. So the backend cuts the letters once.

This doesn't break [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)'s *no
presentation* rule. The letters are **content cut from content** a person typed, like the name
itself, not a sentence the platform wrote. The colour crosses as a **key**, and each client maps it
to its own palette, because design systems aren't shared
([ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §6).

A player's initials (ADR-0167 §3) stay client-cut: one client draws them, and nothing else needs to
agree with it.

### 6. Sport dots are computed when read, never stored

- **A player group's** dots are the sports in which **at least two members hold a Skill rating**,
  because that's what the group can actually play.
- **An official group's** dots are its **declared** sports.

A rating earned or a member leaving moves the dots on the next read, with nothing to keep in step.

### 7. Membership rules

- **Anyone**: joining admits the player at once. Joining twice changes nothing.
- **People I approve**: joining creates a **Join request**. There is at most one pending per
  (group, player).
- **An Administrator acting as a player always joins their own groups directly.** They would
  otherwise be asking themselves.
- **Approving** admits the player at once. **Declining** removes the request **silently**, and the
  player may ask again. Nothing tells them they were declined.
- **Switching to Anyone admits everyone waiting at once**, because nobody should be left waiting
  under a rule that no longer applies. This holds for the Owner's Edit group and for the
  Administrator's settings alike.
- **Leaving**: a member may leave, and may rejoin later under the group's rule. An **Owner leaving a
  group that has other members passes ownership to the longest-standing member**, the one who
  joined earliest. The group always keeps someone who can approve people.
- **Deleting**: a player group may be deleted **only while its Owner is its only member**. That
  undoes a group nobody joined, and it can never take a group away from people in it.
- **Running an official group isn't membership.** The Administrator has no way to delete an
  official group or to stop running it. Only the club moves it (§8) or ends the administratorship
  ([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md) §7).
  An Administrator who **joined as a player** is a Group member like any other, and may leave as one.
- **Nobody removes a member**, not the Owner, not the Administrator, not the club. It's out of scope
  for this release, and the Consequences say what that costs.

### 8. A handover moves who answers, and nothing else

The club may give **any** official group to another **active** Administrator of the club, including
a group whose administrator it removed. The group keeps its link, join policy, WhatsApp size,
members and **waiting requests**. The requests belong to the group, so the new administrator simply
finds them. One event, *administrator assigned*, records it. When nobody can be chosen, the club
website says *Invite an administrator first*.

### 9. Search returns club cards with their groups inside

- **Home-club search** (New group) matches the folded club name or district.
- **Join search** matches the folded club name or district, a group's name, or a group link (§4).
- **The result is always club cards, with groups inside.** A card matched by its club carries all
  its groups. A card matched by a group's name carries only the matching groups. A link carries
  exactly its group. A group is always shown where it lives.
- **The order** is by distance from the caller's Location area, then by name, 20 to a page. A caller
  with no Location area gets A–Z with no distances
  ([ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §6).
- **Each group carries the caller's relation to it**: *member*, *requested*, *none*, or *none*
  where the caller runs it (which means they join directly, §7).

### 10. Blocks hide people in Members lists, and never change a count

A blocked pair, in **either** direction, is left out of **each other's** Members lists in every
group. That is ADR-0095's symmetric effect on a new surface: a block still means the two don't see
each other.

**Counts don't change.** *12 members* is a fact about the group, the same for every reader. A count
that differed by reader would itself tell someone that something was being hidden from them.

### 11. What is counted

- ***N members*** counts every Group member, including an Administrator who joined as a player.
- **The club's *Players* figure is the same count.** One number, whoever reads it.
- ***Games*** counts only **games born in the group**. None exist yet, so it reads 0. It sits
  **behind a port**, so the day a group can pick games, the count fills in without its meaning
  changing. Games two members arranged elsewhere are never counted, because the club would read them
  as the group's work.

### 12. Play opens on Groups, and the flag keeps the bridge

The `find_a_game` flag's **code default becomes off**, and so does its value in every environment's
definition in `Raketa02/raketa-features` ([#521](https://github.com/Raketa02/Raketa/issues/521),
done by hand once [#512](https://github.com/Raketa02/Raketa/issues/512) lands, because until then an
off flag would show a blank Play). Play renders a **Groups | Explore** switch where the placeholder sits
today. **Explore is a blank page** for now. **Turning the flag on restores Find a game**, so the
rebuild never burns the bridge behind it. The five-tab bar is unchanged. The mocks' three-tab bar is
out of scope.

**The backend guards nothing** (ADR-0180 §5). With the flag off, Find a game's endpoints still
answer, and the group endpoints answer whatever the flag says. Turning a screen off hides it and
doesn't close the door behind it. That is still acceptable here, because nothing on either side of
the flag is dangerous to call.

### 13. What a group doesn't do yet

A group doesn't pick games, post games, offer or book courts, or handle money. It has **no chat**,
no friends list and no count badges on its tabs. The Games tab's *"3 of 4"* is read from the members
rated in the selected sport, with their faces in joining order. *Nothing picked right now* is the
honest line once the seats could be filled. The Fill in tab's **+ Post a game** is drawn and does
nothing. Each of these is a later record.

## Consequences

**Easier**

- One link rule, one join path, one page, and one set of membership rules for both kinds.
- A WhatsApp post made today still works after any rename, policy change or handover.
- The club watches its crowd arrive in the same count the group page shows.
- Group-born games can be counted later without redefining *Games*.

**Harder**

- **Every rule branches on kind.** An Owner exists for one kind, declared sports and a WhatsApp size
  for the other, and "can be deleted" for only one. Each rule has to say which kind it binds, and a
  rule that forgets will bind both.
- **The link is a permanent capability, and it can't be rotated.** Anyone holding it can find the
  group and, if the group is *Anyone*, join it. A leaked link can only be answered by switching the
  group to *People I approve*. Rotation was refused because it would kill every post of the link.
  This will be reopened if abuse shows up.
- **Nobody can remove a member.** An unwanted member can only be tolerated, or the group re-made
  without them. That is an honest gap, and the first report of a bad actor in a group reopens it.
- **Ownership passes by seniority, not by activity.** The longest-standing member may be someone who
  never opens the app, and they then hold every waiting request.
- **Dots are computed on read.** A Groups list costs a ratings read per group. That's free at seed
  scale and is the first thing to cache if the list slows down.
- **No name is unique.** Two *Padel Kraków* groups at one club are allowed, and the amber *group
  already here* is the only nudge against a split crowd.
- **The monogram rule lives on the wire.** Changing it changes every client's tile at once, which is
  intended, and it's one more field that every surface carries.
- **Blocks hide rows but not counts.** An attentive reader can see *12 members* above eleven rows.
  That is accepted, because a count that differed by reader would give more away.
- **`find_a_game` off is now the default a first launch sees.** A player who relied on Find a game
  loses it until the flag is turned on for them, and only the flags repo can do that.
