---
paths:
  - "app/modules/groups/**"
---

# Groups and official groups

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A group is a crowd at a home club, and its link never changes**
  ([ADR-0183](../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md),
  #504, #505, #506). `app/modules/groups/` holds **one event-sourced aggregate for both
  kinds** (`player_group_created`, `group_joined`, the Join request's three —
  `join_requested`, `join_request_approved`, `join_request_declined` — #506's five:
  `group_left`, `ownership_passed`, `group_renamed`, `join_policy_changed`,
  `group_deleted` — #509's three, below, and #510's `administrator_assigned`). The
  repository's `save` writes **three projections in the caller's transaction** —
  `groups`, with `name_folded` written from the first event (and again on a rename)
  because SQL cannot fold, `group_members`, whose `joined_version` (the
  admitting event's stream version) is the exact joining order, and
  `group_join_requests`, one row **while a request waits** and deleted by its answer.
  **When an account first joined a group is read off `group_members`**
  (`GroupDirectory.first_joined`, #727): `MIN(joined_at)` per account over the groups it is
  in now — a leave deletes the row, so it is the earliest join *among those*, and an account
  that left every group is in none — which Notifications asks for *Get your level*.
  **A deletion leaves no row in any of the three** — the link then finds nothing, which is
  how it reads *nothing at that link* — and the repository loads a stream ending in
  `group_deleted` as **no group**, so every act on one meets `group_not_found`.
  Five things are load-bearing. **The code is minted with `secrets`** from an alphabet
  with no look-alikes, checked against the table, unique and never changed, and the
  **link is `PUBLIC_SITE_URL` + `/join/` + code** — built in presentation, because the
  address is configuration and a domain may not read it; a deployed environment refuses
  to start without it or with a non-`https://` one. **The monogram is cut here and the
  colour crosses as a key** (0–7, from a SHA-256 of the id), so three clients draw one
  tile; the cut is by what a reader sees as a character, so an emoji or a decomposed
  accent is never halved (`domain/monogram.py`). **Dots and each sport's *N of M* are
  read, never stored** — `domain/sports.py`, over `RatedGroupMembers`, one question about the
  union of every member a response names. **One tap, and the policy decides what it was**:
  `POST /groups/{id}/membership` admits at once under *Anyone* and leaves a Join request
  under *People I approve*, answering the card's row with `relation` `MEMBER` or
  `REQUESTED`; neither is recorded twice. **Approving is admitting** — one event, no
  `group_joined` beside it — and approving somebody with nothing waiting is
  `join_request_not_found`, because nobody is admitted who did not ask; **declining is
  silent** (the relation reads `NONE` again, they may ask again) and declining what is
  not waiting changes nothing. **Nobody but the Owner** sees or answers requests, edits the
  group (`PUT /groups/{id}/details`, name and policy together or neither) or deletes it: a
  stranger — the asker included — meets `group_not_found`, a member `not_the_group_owner`,
  and a member meets that before their name is read. **Switching to *Anyone* admits
  everybody waiting at once** — `join_policy_changed`, then one `join_request_approved`
  per request in the order they asked, answered by whoever switched, so there is one way
  to become a member off a request — and the answer's `admitted` names them. **Leaving**
  (`DELETE /groups/{id}/membership`) is open to every member but an Owner alone
  (`lone_owner_cannot_leave`, who deletes instead); an Owner leaving a group with others in
  it records `ownership_passed` **before** their `group_left`, to the first key of the
  aggregate's joining-ordered `members` — this stay, so a rejoiner counts from their return
  — and the queue passes with it because only `owner_id` moved. **Deleting**
  (`DELETE /groups/{id}`) is the Owner's, only while alone (`group_has_other_members`).
  **Members** (`GET /groups/{id}/members?sport=`) lists only the members rated in the
  sport, the reader, then the Owner, then newest joined first (`domain/members.py`), each
  with **the reader's relation to them** (`relation`, `NONE` on the reader's own row; lent by
  Friends through `MemberRelations`, signed in `groups/infrastructure/friends_member_relations.py`,
  which also signs Friends' `ReadersGroups` — so the arrow runs `groups → friends`; #745,
  `friends.md`), the published Level and **Player reliability** — `player_score` and
  `reliability_band`, copied from their record (`MemberReliability`), and on every row since
  #659: everyone starts at a hundred. It is the one read also open to **whoever runs an official group now**
  (`listing_for_a_member_or_its_runner`, #566), who reads the same rows and is one only once
  they join as a player. **A block hides nobody**, either way round, there or on the Info
  tab's members row that opens it (`member_faces`, up to five, everybody but the reader in
  the Members order), and the Games tab's seats stay the first rated in joining order,
  whoever reads them (ADR-0183 §13, #504): a block keeps two people off one court and
  reaches no group read ([ADR-0193](../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2, superseding ADR-0183 §10; #586 removed `HiddenMembers`). No group read asks the block
  state, so it can fail none of them. The answer to `PUT /details` is still drawn **before
  the commit** (`GroupPages`), so a read that fails there records nothing.
  And **it reads five contexts through ports it
  declares in its own words**, each adapter over the provider's own port: clubs'
  `ClubDirectory` (which `clubs` now publishes over its search projection, folding the
  query itself and escaping `LIKE`), rating's `RatedPlayerQuery` (published Levels for a
  request card and a Members row), users and the Player profile for a face or, name only,
  a group's Owner, the profile's Location area for distance, `player_score`'s
  `PublishedScoreQuery` (`GroupMemberReliability`) — and its domain
  borrows two pure functions, clubs' `fold` and the matcher's distance print, and says
  so where it does. **The two searches answer one card**, `ClubCardSchema`, built by
  `views.club_cards`, and one order — the **printed** distance (`shown_kilometres`, from
  the reader's Location area to the club's point), then the folded name, twenty to a page;
  a reader with no Location area gets A–Z and `distance_km: null`, a blank query answers
  nothing, and a card's groups come the biggest crowd first. Home-club search is
  **`/home-clubs`, never `/clubs`** — anything beginning `/api/v1/club` reads as the club
  surface. Join search is **`/join-search`** (`/groups/search` would read as a group id)
  and matches four ways (`domain/join_search.py`): a club by name or district carries
  **every** group at it, a group by its folded name comes inside its club's card **alone**
  when the club did not match, and **any text containing `/join/<code>` is a link** that
  finds exactly its group and is searched for nothing else — the domain is never read, and
  a link that leads nowhere answers no clubs with `read_as: LINK`, which is *nothing at that
  link* and not *no match*. Each row carries the Owner's **whole nickname** as
  `owner_nickname`, never cut (ADR-0199 §1, #724; the player app draws the *approves joins*
  line). Reading a group is
  members-only and a stranger meets the same `group_not_found` as a missing id. Seeded
  by `app/seeds/groups.py` — four *Anyone* groups owned and joined by the named accounts,
  so the dots follow the rule (no squash or badminton dot: one member rated is not a dot),
  and the protagonist's *People I approve* group, with a member she let in through
  `ApproveJoinRequest` and `rated-in-every-sport`'s request left waiting.
  **An official group has no Owner, and an Administrator runs it from the app** (#509,
  ADR-0183 §3, ADR-0184 §8): `official_group_created` names the `administrator_id` and
  no member — running one is not membership — and `whatsapp_size_set` and
  `sports_declared` are official-only; answering, renaming and the policy reuse the
  player kind's events, every `*_by` the account that tapped. The projection's `kind`
  and a check constraint (migration `0034`) hold the two shapes, and **every rule
  branches on `kind`, never on a null**. Four things are load-bearing. **Who runs it is
  read, never held**: `GroupAdministrators` (over the administrators' directory)
  answers the account and the club's name for them **only while the administratorship
  is active**, so a removal takes the group away on the next read and an orphan
  needs no event. That account **joins directly** under *People I approve*
  (`join(runs_it=…)`), comes second on Members with `is_administrator` — the **admin**
  tag — and is `administrator_nickname` on the approver line: the account's nickname, or
  the name its club typed for an Administrator who has never played (ADR-0199 §4), never
  cut. An official group's dots
  are what it declares, and its page carries `declared_sports`. **The administrator's
  routes are `/administrator/clubs/{club_id}/groups`** behind `AdministratorAtClubDep`
  — create, list, read (players newest first, nobody hidden for a block), approve,
  decline and `PUT …/settings` (all four fields; *Anyone* admits everybody waiting) —
  and a group that administratorship does not run is `group_not_found` whatever the
  reason. **Nothing deletes one, and its Administrator cannot stop running it**: there
  is no such route, and the player surface's Owner acts meet `not_the_group_owner`; an
  Administrator who joined as a player leaves as one and still runs it. And **the club
  cannot untick a sport one declares**: `ChangeClubDetails` asks `OfficialGroupSports`,
  clubs' demand **signed in `groups/infrastructure/`** so the arrow runs `groups →
  clubs` only (an `.importlinter` contract), and answers `409
  club_sport_declared_by_group` naming the group. **Its courts are its club's, hour by
  hour** (#746; ADR-0202 §7): at an hour its club has a free court of the sport, only the
  club's are offered; at an hour it has none, other clubs within the club's distance too,
  each marked as offered because the club is full — unless the club switched other clubs'
  courts off (on by default). A player group is unchanged: home first, then within 10 km,
  at every hour. One court source serves the deck, Post a game and the friends card
  (#750; `proposals.md`, *Where*). Seeded by `app/seeds/official_groups.py`
  after the administrators: Marta's *Ogrody 33 Club* (*People I approve*, 48, padel,
  three players, one waiting) and *Ogrody open play*, run by `rated-in-every-sport`,
  who plays in it; and `app/seeds/full_hour.py` closes every Ogrody 33 court on the first
  Saturday at 10:00 from two days out, so both are offered other clubs then and only
  Ogrody 33 at its other hours.
  **The club watches its official groups and hands them over, on the club surface**
  (#510, ADR-0183 §8, §11). `GET /api/v1/club/groups` is the Groups table — every
  official group at the club, by name: who runs it (`administrator`, the name the club
  gave them, or `null` — *needs an administrator*), `member_count` (the group's own
  count, an Administrator who plays included), `waiting_count`, `whatsapp_size` and
  `whatsapp_percent` (rounded half up by `WhatsAppSize.percent_arrived`, **never
  capped**), and `games`. **`games` is the games booked in the group** (ADR-0189 §8),
  read through `GroupBornGames` — answered by `BookingsGroupBornGames`, **signed in
  `proposals/infrastructure/`**, because a group's pool is filed under the group's id and
  that is Proposals' fact: the bookings in its pool, every one counted (#542). `groups`
  knows neither proposals nor bookings. `PUT …/groups/{id}/administrator`
  is the handover: one `administrator_assigned` event and nothing else moves — the
  link, the policy, the size, the members and **the waiting requests**, which the new
  Administrator simply finds; anything but the club's official group is
  `group_not_found`, anybody but an **active** Administrator of the club is `409
  administrator_not_active`, and handing it to whoever runs it records nothing.
  **The club answers an official group's Join requests itself, at any time**
  ([ADR-0191](../../../docs/adr/0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md)
  §1): `GET …/groups/{id}/requests` (the `nickname` and the Levels, no photograph, #725) and
  `POST …/requests/{player_id}/approve|decline`, the Administrator's rules and events,
  answered `as_club` with the Club account as `approved_by` — the only two acts the
  aggregate lets a club do, and never on a player group at its courts. Answering is not
  running: the group still needs an administrator until a handover. **A handover is told to
  whom it was handed, once** (ADR-0192): `administrator_assigned` sets the projection's
  `handed_over_at`, `handover_seen` clears it, `/users/me` lists the untold ones as
  `profiles.handovers` (through `OfficialGroupAssignments.handed_untold`), and
  `POST /administrator/clubs/{club_id}/handovers/seen` steps over anything it cannot apply.
  Because who runs a group stays **read, never held**, two things follow and are
  pinned: the club's *Reset password* (back to *invited*) leaves that person's groups
  needing an administrator until they set a new password, and **somebody removed and
  invited back runs again the groups nobody was handed meanwhile**. The Administrators
  table's *groups* column is filled on active rows only, through
  `OfficialGroupAssignments` — administrators' demand, **signed in
  `groups/infrastructure/`** like clubs' sports question, and held by its own
  `.importlinter` contract. And the member's page, `GET /groups/{id}`, carries the
  card's `administrator_nickname` and `is_administrator` (one `approver_name` for both),
  so the Info tab reads *[club] approves joins* for an orphan, as the search row does.
