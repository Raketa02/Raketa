---
paths:
  - "app/modules/friends/**"
  - "app/seeds/friends.py"
  - "app/modules/groups/infrastructure/friends_*.py"
  - "app/modules/proposals/infrastructure/friends.py"
  - "app/modules/proposals/application/friends.py"
  - "app/modules/player_record/infrastructure/friends_relations.py"
---

# Friends

Decisions that are load-bearing and not obvious from the code (#745;
[ADR-0202](../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§1–§2, §8; [`docs/specs/friends/`](../../../docs/specs/friends/README.md), the mechanics §3, §12;
the words §29.1–§29.3).

- **A Friendship per pair, event-sourced, and a projection beside it.** `app/modules/friends/`
  holds one aggregate, **one stream per unordered pair** (`domain/ids.py`: `uuid5` over the
  sorted pair, its own namespace — the opposite of a Block's ordered pair, because a friendship
  is one fact about two people and the two requests that could stand between them are
  exclusive). **At most one thing stands between two players**: a friendship, or one open
  request — a second request **crosses** the first and they are friends at once — so the state
  is `are_friends` and at most one `OpenRequest`. Six events, all v1:
  `friends.friend_requested`, `…friend_request_set_aside`, `…friend_request_cancelled`,
  `…friend_request_crossed` (followed in the same act by `…friends_made`), `…friends_made`
  (`how` `ACCEPTED` or `CROSSED`; `requester_id` asked first), `…friendship_ended` (`how`
  `REMOVED` or `BLOCKED`, `ended_by`). **Every rule is the aggregate's**: no self-request
  (`cannot_befriend_yourself`), none to a friend (`already_friends`), none while your own is
  open, set aside or not (`friend_request_already_sent`); only the person asked accepts or sets
  aside (`friend_request_not_found` otherwise); a cancel, a removal and a block are **no-ops**
  when there is nothing to take back, so their routes answer `204` either way. **The projection
  is `friend_relations`** (migration 0063): **the reader's side of the pair**, two rows while
  something stands — `FRIEND`/`FRIEND` or `SENT`/`ASKED_YOU` — none once nothing does, with
  `since`, `set_aside` and where a request was made, rewritten whole by the repository's `save`
  in the caller's transaction. Keyed `(player_id, other_id)`: every read is the reader's side
  alone (`FriendshipDirectory.rows_of`), and **no method answers about two other people** — the
  property *Kuba never learns that Tomek and Magda are friends* rests on. A projection rather
  than Blocks' payload scan, because every face on every deck asks it (ADR-0197's budget).
- **The use case adds two rules the aggregate cannot know** (`application/requests.py`):
  - **a request is open to people from your groups** — the requester must share a group with
    them **now** (`ReadersGroups`, signed in `groups/infrastructure/`), else
    `player_not_in_your_groups`, one body for a stranger and an id nobody holds; a request made
    by `LINK` (#748's) is the one way in from outside and skips it;
  - **nobody asks somebody they blocked** (`unblock_them_first`) — it would offer friendship
    across their own block; it names only the reader's own block. A call made without a ruling:
    the mechanics say only that the record never offers it, and Members' **+ Add** shows on
    everybody not a friend, since no block crosses on Members (ADR-0193 §2).
- **A block ends a friendship; a blocked player's request is hidden, live**
  (ADR-0202 §2). `EndFriendshipsOnABlock`, an outbox subscriber to **both** versions of
  `blocks.player_blocked`, added per delivery run over its session (`subscribe_the_block_ender`,
  `app/bootstrap/events.py`), records `FriendshipEnded` (`BLOCKED`) when either player blocks
  the other and something stands — the friendship **or an open request**; owed by the block
  being recorded, so a block lifted before delivery still ended it, and **unblocking brings
  nothing back**. **A request asked while the addressee has blocked the requester is recorded
  `unseen`** (`FriendRequested.unseen`, decided by the use case from the addressee's own blocks
  and never answered): the requester reads `SENT` for ever, exactly what a request set aside
  shows, and the addressee has **no row at all** — `NONE` on every face and pill, off *Asked
  you*, off Home, never told, **not after an unblock either** (the mechanics §3.5: *Tomek never
  sees it*), and an accept or *Not now* of it is `friend_request_not_found`. If the addressee
  later asks the requester, the two cross as any requests do. **A request asked before a block
  whose delivery has not ended it yet** is hidden at every read by `application/reads.py`'s
  `as_the_reader_sees`, live, over `ReadersBlocks` — the reader's **own** blocks through
  `BlockQuery.blocks_made_by`, failing closed as that port does — read only when a row is an
  `ASKED_YOU`. Who blocked the reader is never read: a member who blocked the reader still
  counts *to add*.
- **Only the reader's relations cross, lent through ports the readers declare**
  (`FriendRelation`: `NONE · SENT · ASKED_YOU · FRIEND`, `domain/relation.py` — the one wire enum
  every surface carries). `ReadRelations.relations_of` answers everybody asked, `NONE` for the
  reader; **`friends_among` is what a face asks** and reads no block (a block ends a
  friendship). The readers, each signed on its own side so Friends imports none of them
  (`.importlinter`'s *friends-knows-none-of-its-readers*):
  - **Members** — `MemberRelations` (`groups/infrastructure/friends_member_relations.py`):
    `relation` on every row, `NONE` on the reader's. The administrator's view draws no pills,
    a client's decision: the row carries it all the same;
  - **the record** — the twelfth demand, `RelationsOfTheReader`
    (`player_record/infrastructure/friends_relations.py`), in the record's own spelling
    `RecordRelation` held to Friends' by a test and put on the wire as `FriendRelation`:
    `relation`, `NONE` on your own record, asked once admitted and never a gate;
  - **proposals' faces** — `ReaderRelations` (`proposals/infrastructure/friends.py`): **faces
    carry only `friend`** — `DeckPerson.friend`, marked for the reader by
    `application/friends.py`'s `with_the_readers_friends` in the deck, a game's details, Home,
    a booked game's details, Fill in and Post a game's slot sheet (`DeckTileSchema.friend`,
    `BookedTileSchema.friend`, `SlotFitSchema.friend`) —
    and the result's *PLAYED WITH* card the whole relation: `GET /bookings/{id}`'s
    `played_with`, everybody else on the game, empty for a reader not on it;
  - **Home's friend requests** — `FriendRequestsOnHome` (`ReadRequestsOnHome`): `GET /home`'s
    `friend_requests`, newest first, each with the requester's face and nickname, `by_link`,
    the group it was asked from **while both are in it now** (read live, so a leaver's card
    names none), the sport, their Level in it and their reliability — open, not set aside, not
    hidden. Not counted in `needing_you`;
  - **the bell** — Notifications' `Friendships` (`FriendsOfTheReader`, below).
- **Where a request was made** is the request's: `RequestOrigin` `MEMBERS · RECORD · RESULT ·
  LINK`, and the screen's `group_id` and `sport` when it showed them (`Where`; a link's names
  neither). The phone sends the first three (`AskedFrom`, `POST /friends/requests`); `LINK` is
  never sent — it is #748's link opening. **The group is kept only if the two share it at
  asking**, so a notice never names a group a client merely sent; the Home card names it only
  while both are still in it.
- **The routes** (player surface, `presentation/routes.py`): `POST /friends/requests` (answers
  `SENT`, or `FRIEND` when it crossed), `POST /friends/requests/{player_id}/acceptance`,
  `POST …/set-aside` (`204`), `DELETE /friends/requests/{player_id}` (cancel, `204` always),
  `DELETE /friends/{player_id}` (remove, `204` always, **no game touched**), `GET /friends`
  (alphabetical, every sport they are rated in with the Level and the band's name; with `sport`
  that one sport alone — empty when unrated — highest Level first, unrated last: calls 4 and
  11), `GET /friends/requests?direction=ASKED_YOU|YOU_ASKED` (newest first; `set_aside` on
  *Asked you* only — whether yours was set aside is never said), `GET /friends/groups` (each of
  the reader's groups with `member_count` and `to_add`: not the reader, no friend, no open
  request either way, nobody the reader blocked).
- **Two notices, both always on, pushed and in the bell** (`notifications.md`):
  `FRIEND_REQUEST` — *{nickname} wants to be your friend* / *With you in {group} · {Sport}*
  (*Invited you to Raketa* by link, `reason` `BY_LINK`; *Answer it on Home.* from a screen with no
  group — a call)
  — to the person asked, **once per request** (keyed by the delivered event) and **only while
  its card is on their Home at delivery**, so a request cancelled, answered or set aside before
  it, or a hidden one, is told nobody; and `FRIENDS_MADE` — *{nickname} said yes — you're
  friends* to whoever asked, *You and {nickname} are friends now* to both when crossed
  (`reason` `CROSSED`), while they still are, with the body *Find {nickname} in You › Friends.*
  (a call). Both are about no game: the group rides as `pool_id`, the person as `people[0]` —
  `player_id` on the wire and in the push data — and `FRIENDS_MADE` opens `RECORD`.
  **A request's row leaves the list and the bell's number once its card leaves Home**:
  `ReadRecentNotices` asks `NoticeDirectory.of_kind` for the reader's `FRIEND_REQUEST` rows and
  `Friendships.waiting_on` for the requests on Home, and leaves out (`recent(…, leaving_out=)`,
  one reading for the rows and the count) every row whose `(people[0], given_at)` is not a
  waiting `(requester, asked_at)` — the notice is given at the request's own instant.
  *Not now*, a cancel, a removal and a block tell nobody.
- **Seeded by `app/seeds/friends.py`**, after the rooms and before the screens, through the
  use cases: the protagonist's friends (`rating-well-established`, accepted;
  `the-one-sport-player`, crossed), a request on her Home (`rating-barely-established`), one
  set aside (`assessment-completed`), one of hers unanswered (`brand-new-player`), and the
  block case off her screens — the `blank-week-player` and `rated-in-every-sport`, friends in
  *Błonia po pracy* until the first blocked the second; the layer drains the outbox
  (`deliver_everything_told`) so the block ends the friendship before the request made since,
  which reads `SENT` and is hidden from the blocker. Each pair is read first, so a second run
  asks nobody twice; `_refuse_a_seed_that_lies` fails the run by name.
- **Tested** over HTTP in `tests/api/test_friends.py` (every scene, the notices, the bell),
  `tests/api/test_friends_on_every_face.py` (each surface's tag, *PLAYED WITH*, Home's
  requests) and `tests/api/test_seed_friends.py`; the four lent ports in the record's,
  proposals' and notifications' demand registers (`tests/demands/friends_world.py` arranges
  them through the aggregates).
- **Not built here**: the Friend link (#748), asking for a level (#749), the friends card and
  the friends game (#750–#752). `Where(made_from=LINK)` and `by_link` are ready for #748.
