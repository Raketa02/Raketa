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

Decisions that are load-bearing and not obvious from the code (#745, #748, #749, #764;
[ADR-0202](../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§1–§2, §4 and its 2026-11-07 amendment, §8; [`docs/specs/friends/`](../../../docs/specs/friends/README.md),
the mechanics §3, §5, §5.1, §12; the words §29.1–§29.3, §29.5).

- **A Friendship per pair, event-sourced, and two projections beside it.** `app/modules/friends/`
  holds two aggregates — the Friendship, and the Friend link (below). The Friendship is **one
  stream per unordered pair** (`domain/ids.py`: `uuid5` over the
  sorted pair, its own namespace — the opposite of a Block's ordered pair, because a friendship
  is one fact about two people and the two requests that could stand between them are
  exclusive). **At most one thing stands between two players**: a friendship, or one open
  request — a second request **crosses** the first and they are friends at once — so the state
  is `are_friends` and at most one `OpenRequest` — and every ask for a level either made of the
  other (below), which nothing ends. Ten events, all v1, the asks' three among them:
  `friends.friend_requested`, `…friend_request_set_aside`, `…friend_request_cancelled`,
  `…friend_request_crossed` (followed in the same act by `…friends_made`), `…friends_made`
  (`how` `ACCEPTED` or `CROSSED`; `requester_id` asked first), `…friendship_ended` (`how`
  `REMOVED` or `BLOCKED`, `ended_by`), the link's `…friend_request_brought_back` (below), and
  `…level_asked`, `…level_got` and `…level_ask_set_aside` (*Ask for a level*, below).
  **Every rule is the aggregate's**: no self-request (`cannot_befriend_yourself`), none to a
  friend (`already_friends`), none while your own is open, set aside or not
  (`friend_request_already_sent`); only the person asked accepts or sets
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
    by `LINK` (the link's opening, below) is the one way in from outside and skips it;
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
  - **Home's asks for a level** — `LevelAsksOnHome` (`ReadLevelAsksOnHome`, #764, below):
    `GET /home`'s `level_asks`, one card per sport;
  - **the bell** — Notifications' `Friendships` (`FriendsOfTheReader`, below).
- **Where a request was made** is the request's: `RequestOrigin` `MEMBERS · RECORD · RESULT ·
  LINK`, and the screen's `group_id` and `sport` when it showed them (`Where`; a link's names
  neither). The phone sends the first three (`AskedFrom`, `POST /friends/requests`); `LINK` is
  never sent — it is the link's opening (#748). **The group is kept only if the two share it at
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
  request either way, nobody the reader blocked), and since #764
  `POST /friends/level-asks/{sport}/set-aside` (*Not now* on an ask's Home card, `204` always,
  below).
- **Two notices about a friendship, both always on, pushed and in the bell**
  (`notifications.md`; the asks for a level have two more, below):
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
  which reads `SENT` and is hidden from the blocker. **And her Home's ASKED FOR A LEVEL** (#764):
  `rating-well-established` asks her for a **squash** level — she is rated in padel and tennis
  — from *Czwartkowy padel*, through `AskForALevel`, read back off `ReadLevelAsksOnHome`. Each
  pair is read first (an ask through `LevelsAskedByTheReader`), so a second run asks nobody
  twice; `_refuse_a_seed_that_lies` fails the run by name.
- **Tested** over HTTP in `tests/api/test_friends.py` (every scene, the notices, the bell),
  `tests/api/test_friend_link.py` (the code, New link, every opening case, the public read),
  `tests/api/test_friends_on_every_face.py` (each surface's tag, *PLAYED WITH*, Home's
  requests), `tests/api/test_level_asks.py` (the ask, every refusal, both notices, two askers),
  `tests/api/test_level_asks_on_home.py` (the card, Not now, the bell, every way it ends) and
  `tests/api/test_seed_friends.py`; the aggregate's asks in `tests/unit/test_level_asks.py`
  and the answerer's two paths in `tests/unit/test_answer_the_asks_for_a_level.py`; the five
  lent ports in the record's,
  proposals' and notifications' demand registers (`tests/demands/friends_world.py` arranges
  them through the aggregates).
- **The Friend link** (#748; the mechanics §4; `domain/link.py`, `application/link.py`) — a
  second aggregate, **one stream per player** (`friend_link_id`: `uuid5`, its own namespace,
  over the owner), two events, v1: `friends.friend_link_made` (on the owner's **first read**)
  and `…friend_link_replaced` (**New link**: `code`, `replaced_code`). **The code is in the
  events**, as a group's is in `groups.created`: an address posted to chats on purpose, not a
  credential — ADR-0184 §4 is about what signs somebody in. `FriendLinkCode` is a group code's
  shape, **spelled twice** because Friends imports no group, held equal by
  `tests/unit/test_friend_link_code.py`; read lower-cased, and anything that could be no
  link's is `friend_link_not_found` like a code never made. **`friend_link_codes`** (migration
  0064) holds **every code ever carried**, `current` false once replaced and never true
  again, written by the repository from the events it appends (a replaced code is not in the
  state); the minter (`RandomFriendLinkCodes`, `secrets`) checks every row, so **no code is
  reused**, and the primary key is the guard behind it. A first read writes; two that race
  are `concurrent_modification`, and the retry reads the winner's code.
- **Opening a link records the owner's request to the opener** (`OpenAFriendLink`), made by
  `LINK`, **asking for no group in common** — Home's *Invited you to Raketa*, its notice
  `BY_LINK`. It answers **the opener's relation to the owner** (`OpenedFriendLinkResponse`):
  - **your own link**: `NONE`, nothing recorded;
  - **a friend's**: `FRIEND`, nothing;
  - **the opener's own request open**: the aggregate crosses it, `FRIEND`, both told;
  - **the owner's request open already**: no second one, `ASKED_YOU`. **One the opener set
    aside comes back to Home** (`Friendship.bring_back`, `friends.friend_request_brought_back`,
    told nobody — its notice row, if it was told, returns to the bell with the card). **A
    call** the mechanics §12 left to this ticket and #756: opening the owner's link is asking
    to see the owner's request, and *Not now* was the opener's to take back. **One recorded
    `unseen` stays hidden** — asked while the opener had blocked the owner, it is one they
    never see, and unblocking brings nothing back (§3.5); its card would name the group, and
    tell them the owner asked across their block. Answered `ASKED_YOU` all the same, never
    `NONE`, which means *your own link*;
  - **the owner blocked the opener**: **swallowed** — nothing recorded, and the answer is
    `ASKED_YOU`, exactly a request's, so the opener lands on an empty Home (the cost ADR-0202
    names). The owner's blocks are read to decide and never answered;
  - **the opener blocked the owner**: `unblock_them_first`, as asking them would be — **a
    call**: the mechanics list the four cases above and say nobody is offered friendship with
    somebody they blocked;
  - **replaced, never made, or no code's shape**: `friend_link_not_found`.
- **The link routes** (`presentation/link_routes.py`, player surface): `GET /friends/link`
  (`code`, `link` = `<PUBLIC_SITE_URL>/f/<code>`; made on first read),
  `POST /friends/link/replacement` (New link), `POST /friends/links/{code}/opening`. **The
  public read** (`presentation/public_routes.py`, `/api/v1/public/friend-links/{code}`,
  `ReadAFriendLink`): the owner's `nickname` and `photo_url`, **nothing else** — an owner
  nobody can name (`FriendFace.nickname` `None`: an account gone) reads as not found there.
  **The opening does not check it**: no account can be deleted yet, and a request from one
  would be left off every list as any nameless row is; when deletion lands, it ends the
  owner's link too. Requests made through a replaced code stay.
- **Seeded**: every named account (`ACCOUNTS`) reads its link through `ReadYourFriendLink`
  in the friends layer — made on the first run, the same code after — and the report prints
  them.
- **Ask for a level** (#749; ADR-0202 §4; the mechanics §5) — **on the Friendship stream**,
  not an aggregate of its own: *once per sport per pair* is a fact about the pair, and an ask
  races a removal on the one stream. Two events, v1: `friends.level_asked` (`asker_id`,
  `friend_id`, `sport`, `group_id`) and `friends.level_got` (the same four). The state keeps
  every ask either side made of the other, `(asker, sport)` → `LevelAsk`, **through a
  friendship's end** (`FriendshipEnded` clears the request and the friendship, never the
  asks), so one removed and made again asks nobody twice. `POST /friends/{player_id}/level-asks`
  (`{sport, group_id}`, `204`), refused **in this order**, so nothing about a stranger is read
  out:
  - `friend_not_found` (404) — not the asker's friend, or the asker themselves; checked before
    anything else is read, so whether a non-friend has a level is never learnt;
  - `not_one_of_your_groups` (404) — `group_id` is no group the asker is in now (one answer
    for a group that does not exist). **A call**: the PRD names the group the ask was made from
    and the client ticket opens its picker, so the ask always names one of the asker's; a
    request merely drops a group the two do not share, but an ask's group is where its answer
    opens;
  - `already_has_a_level` (409) — the friend has a published Level in the sport
    (`FriendLevels`, rating's `published_for`: any rating at all);
  - `level_already_asked` (409) — the aggregate's, answered or not, ever.

  **The answer**: `AnswerTheAsksForALevel` (`handlers/level_got.py`), added per delivery run
  over its session (`subscribe_the_level_answerer`, `app/bootstrap/events.py`), records
  `friends.level_got` (`Friendship.answer_the_ask`) on the pair's stream, **whether or not they
  are still friends** (Notifications tells only while they are). It hears **two** events:
  - `rating.rating_initialised` — a rating's stream is keyed on the player and the sport, so the
    event *is* the first level — answering each asker waiting on it;
  - `friends.level_asked` — an ask whose friend has a level in the sport **already**, read
    again (`FriendLevels`) after the ask's commit: a level recorded between the use case's check
    and its commit, and delivered first, found no ask to answer. Whichever commit lands second,
    its delivery sees the first. The friend is still told *level asked* in that window — a cost
    left open.

  An ask already answered records nothing, so a delivery seen twice, or an ask answered on both
  paths, tells nobody twice.
  **The projection is `friend_level_asks`** (migration 0065): one row per asker, friend and
  sport (the primary key), the group, `asked_at`, `got_at` — rewritten for the pair by the
  repository's `save` when an ask or an answer is appended. **Two ports for two audiences**,
  one adapter (`SqlAlchemyLevelAskDirectory`): `LevelsAskedByTheReader.sports_asked_by(asker,
  among=)`, from the reader's side (the picker's *Asked*), handed to `ReadFriends`; and
  `AsksWaitingOnALevel.askers_waiting_on(friend, sport)`, handed **to the answerer alone** — it
  names who asked somebody else, so the property is the port's, not its callers'.
  **Two calls left open**: an ask is not checked against the sports the group plays (the
  client sends its picker's group and sport together); and an ask told nobody — the two no
  longer friends at its delivery — still uses up the one ask, ever. **The friends read**
  carries `level_asked_in` per friend: the sports **the reader** asked them for, in the
  registry's order, or with `sport` that one or nothing — **a set-aside ask included**: the
  asker never learns it, so *Asked* cannot tell it from one unseen. Notices: `LEVEL_ASKED` /
  `LEVEL_GOT` (`notifications.md`).
- **An ask waits on the friend's Home until they have the level or say Not now** (#764;
  ADR-0202 §4's 2026-11-07 amendment, Q129; the mechanics §5.1). **The read is
  `ReadLevelAsksWaiting`** (`application/reads.py`), over a third port onto the asks'
  projection, `LevelAsksOfTheReader.asks_of(reader)` — the asks made **of** the reader, not
  answered and not set aside, from the reader's side (who asked them) — and lists an ask while,
  **each read live and recorded nowhere**, its asker is **the reader's friend now**
  (`FriendshipDirectory`), **not blocked by the reader** (`ReadersBlocks`, so the reader's own
  block takes them off before its delivery ends the friendship; an asker's block of the reader
  once its delivery has), and the reader holds **no level in the sport** (`FriendLevels`, so a
  level got by any route takes the card off before *level got* is delivered). Newest first, a
  tie by asker id, then sport. `ReadLevelAsksOnHome` groups it **one card per sport, the sport with the
  newest ask first**, its askers newest first with their faces (a nameless one left off, as a
  request's is) — `GET /home`'s `level_asks` through Proposals' `LevelAsksOnHome`, signed in
  `proposals/infrastructure/friends.py` (`FriendsLevelAsksOnHome`). Not in `needing_you`; no
  group is named. **Not now** is `POST /friends/level-asks/{sport}/set-aside`
  (`SetAsideTheAsksForALevel`, `level_asks.py`): it sets aside **every ask in the sport that
  `ReadLevelAsksWaiting` lists at that instant** — `Friendship.set_aside_the_ask(by=, sport=)`,
  `friends.level_ask_set_aside` v1 (`asker_id`, `friend_id`, `sport`), one per pair, one
  transaction — and `204` with nothing listed. **Only the friend asked**: the press addresses the
  ask made *of* `by`, so an asker's own press touches nothing of theirs; an answered or
  set-aside ask is a no-op. A set-aside ask **is still waiting**: `got_at` and the answerer
  ignore it, so the first level answers it and every asker is told *level got*. **Nobody is
  told** — the event is heard by the audit line alone. Projected as
  `friend_level_asks.set_aside_at` (migration 0067), written by the repository's `save` with the
  ask's other columns. **Calls this ticket kept**: a friend removed and made again whose ask
  was never set aside is back on the card (the friendship is read live) and one set aside stays
  aside; and *Not now* while an asker is no friend (or blocked) sets aside nothing of theirs,
  since Home did not list it — so their ask is back with them. The bell's half is
  `notifications.md`'s.
- **The friends card is Proposals'** (#750; `proposals.md`): it asks this context only
  `ReaderRelations.friends_among` — the reader's friends now, `not_a_friend` otherwise.
- **Not built here**: the friends game (#751–#752).
