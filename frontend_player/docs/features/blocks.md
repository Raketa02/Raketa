# blocks — Block on the record, Blocked players under You › Account

The client side of the backend's **Blocks** context: a player keeps somebody off their games from
that person's record, and undoes it from a list under You › Account (the record's own _Unblock_ went
with #779, below). Built by
[#587](https://github.com/Rakieta02/Rakieta/issues/587) for PRD
[#571](https://github.com/Rakieta02/Rakieta/issues/571), on the contract
[#586](https://github.com/Rakieta02/Rakieta/issues/586) built, and decided by
[ADR-0193](../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md).
`player_record`'s sheet draws `BlockRow` at the foot of every record but your own; the shell
composes `BlockedPlayersRow` into the You tab's **ACCOUNT** group under _Notifications_; the
screen is `/you/blocked-players`. The walks are `components/blocks.test.tsx`.

**A feature of its own, because the act is not the record's.** The record says one thing about a
block — whether the reader made one of its subject, `blocked_by_you` — and `player_record` folds
it at its wire boundary. The three routes, the list and its screen, and the confirm sheet are this
feature's, as the backend's are its `blocks` context's. So the record imports `BlockRow` and hands
it the subject, the name, the record's answer **and the record's own re-read** (`rereadRecord`):
this feature never names `player_record`'s keys, because that feature drawing this one's row while
this one reached back for its keys would be a dependency both ways, which architecture Part 1 calls
a defect. It does import `proposalKeys`, for the games a block reaches, as `notifications` does.

**The row is the record's answer, never a guess.** _Block Kuba Wiśniewski_ while
`blockedByYou` is `false`, _Unblock Kuba Wiśniewski_ while it is `true`, and **no row** where it is
absent — which the mapper makes true on your own record (the server answers `false` there, and a
`false` is a row) and where the server could not read the blocks (it omits the field rather than
guessing, and so does the sheet). A press writes and then **re-reads the record before it
settles**, so the row flips on the server's next answer and the sheet's _Block_ stays busy until
the record under it already says _Unblock_.

**The words are the whole name, and there is no pronoun.** PRD #571 proposed _Block Kuba_ and
_"You won't be put in games with Kuba. He isn't told."_, and said the design pass may refine them.
ADR-0171 §4 refines the first: every sentence naming somebody uses the whole name, and a row's
label is its spoken name, so it is _Block Kuba Wiśniewski_ (the button's box may cut the drawing on
a long name; the spoken name never is). The second needed a pronoun this app does not have: the
only thing that could say whether Kuba is _he_ is the gender answer, which the gender step promises
nobody is shown. So the sheet says _"You won't be put in games with Kuba Wiśniewski. They aren't
told."_ under the title _Block Kuba Wiśniewski?_ — `blocksCopy`, one module, if the product owner
wants the first name after all.

**Block asks first; Unblock does not.** A block can cost the blocker a game — their yeses where
the other person is In are taken back, and nothing brings them back — and ADR-0193 says the sheet
must say what blocking does _because nothing afterwards will_. It is the departure's shape
(`ExitDoor`, `LeaveSheet`) with the links sheet's two buttons: _Block_ (6.1's primary, the act
named once) over _Cancel_ (secondary), and the sheet's close named _Not now_ so two controls never
share a name. **Cancel changes nothing.** An unblock costs nothing and returns nothing, and a
second block is one sheet away, so it happens on the press, on the record and on the list alike.

**The confirm sheet is the first sheet over a sheet.** It is a child of the record's content, so on
iOS its native window is presented from the record's, and on Android `OverlayHost` lays it as the
next layer up — which needed one change in `shared/ui`: a layer under a newer one is hidden from a
screen reader (`covered`), as the app beneath every layer already was, and the back answers the
newer first (`_shared.md`). The row is hidden while the sheet is up, as `ExitDoor`'s door is.

**What a block re-reads is what it moves** (`useBlockWrites`). Both writes re-read Blocked players,
the subject's record where it is open (a record is never cached between opens, so an unblock on the
list has none to re-read), and **every group's deck** — and with it each group's Fill in and posting
reads, which sit under the group's root — rather than the one the record was opened from: a block
keeps the pair off one court in every group they share. A block also re-reads what its withdrawal
moves (ADR-0193 §4): the live yeses, a game still filling in detail, Home and a booking in detail —
a game waiting for one payment drops back to filling as though the reader left it, so these are the
reads leaving a booking re-reads. An unblock brings no yes back and re-reads none of them. On the
list, an unblock also takes the row out at once — the answer is certain — and the re-read agrees.

**Twice is nothing, and offline waits.** Both routes are idempotent, which is the correctness
mechanism under a double tap. A block that lost a race with another block of the same person
answers `concurrent_modification`, whose retry is the contract's own no-op, so that one code is
retried once — the global rule retries no mutation, and this is the stated reason. Offline, a write
is held and an amber line says so where it was pressed (`WriteNote`, which also says a refusal); **closing the confirm sheet takes a held
block back** out of the queue (the group exit's rule, #529 F5), so it is never sent on a reconnect
the player did not choose. A held unblock is left to resume: it is harmless, and there is no sheet
to close.

**Blocked players** is the server's list in its order, newest first, and only the reader's own
blocks: each row is the face (`PlayerPhoto` at 7.19's 38 — their photograph or their generated
poster), the whole name, and _Unblock_ drawn, spoken _Unblock Kuba Wiśniewski_, since a column of
_Unblock_s names nobody. Empty is _You haven't blocked anyone._, the contract's own words; a
failure is the recovery sentence with _Try again_, never an empty list; offline is the amber line.
The row on You says _Nobody_, _1 player_ or _2 players_ off the same read, so an unblock on the
screen is on the row when the player comes back. When each block was made crosses on the wire and
is not carried: nothing draws it.

**Not seen on a device**: the confirm sheet rising over the record on both platforms, TalkBack
inside the stacked sheet, the row at the record's foot under a long name, and the list's rows.

**The row and the list name the nickname** ([#728](https://github.com/Rakieta02/Rakieta/issues/728), [ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). `BlockedPlayer.name` is mapped from
the wire's `nickname`, and the record hands the row its `nickname`, so the row reads _Block kuba.w_,
the sheet _Block kuba.w?_ and _"You won't be put in games with kuba.w. They aren't told."_ — whole,
never with an @, and the paragraph above read through ADR-0199 §7.

**Block is half a row now, and Unblock the whole of it** ([#753](https://github.com/Rakieta02/Rakieta/issues/753);
the friends screens §2). The record's foot became _Add friend_ beside _Block_, so the row draws
**_Block_** and **_Unblock_** (`BLOCKS_COPY.row`) and still speaks _Block kuba.w_ / _Unblock kuba.w_ —
a half-width button cannot hold the whole nickname, and the spoken name was always the one that
mattered (the paragraph on the whole name above). On somebody the reader blocked, _Unblock_ stands
alone and full width, and `friends` offers nothing beside it (the friends mechanics §3.5). The step
above the row moved to the record's foot, which holds both buttons. A block also ends a friendship
on the server (ADR-0202 §2); the record's re-read after it shows that, and nothing here names it.

**Unblock left the record, and a block closes it** ([#779](https://github.com/Rakieta02/Rakieta/issues/779);
[ADR-0203](../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8; the rankings
screens §6; the words §30.8). Since #773 a record never opens between two people either of whom
blocked the other, so the row is always _Block_: `BlockRow` lost its `blocked` prop, its _Unblock_
and the record's re-read, and is handed the record's close instead (`onBlocked`). **Once the block
stands** — after everything it moved has been read again, so the sheet's _Block_ stays busy until
then — the confirm sheet and the record close together; the record is not read again, because that
read would be refused. **The confirm sheet now ends _You can unblock from You › Blocked players._**
(§30.8, a call), the one way back, and `friends`' refusal for asking somebody you blocked names the
same place. When _Block_ stands alone is [`friends.md`](friends.md)'s rule. The paragraphs above that put _Unblock_ on the record, read `blockedByYou`, or have a block re-read the
record describe #587–#753 and are superseded here; Blocked players and its _Unblock_ are unchanged.
**Not seen on a device**: the confirm sheet and the record closing at once, a layer over a layer on
Android.
