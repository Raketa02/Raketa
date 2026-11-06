# friends — requests, Members' pills, the record's Add friend, Home's FRIEND REQUESTS

The client side of the backend's **Friends** context: a player asks a group-mate to be friends from
Members or from their record, answers a request on Home, and sees who is a friend on every face.
Built by [#753](https://github.com/Raketa02/Raketa/issues/753) for PRD
[#743](https://github.com/Raketa02/Raketa/issues/743), on the contract
[#745](https://github.com/Raketa02/Raketa/issues/745) built, and decided by
[ADR-0202](../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§1–§2. The screens are [the friends spec set](../../../docs/specs/friends/the-screens.md) §1, §2 and
§6.2; every sentence is [the words §29.1–§29.2](../../../docs/specs/matchmaking/the-words.md#29-friends).
The walks are `components/friends.test.tsx`; the tags on faces are walked in the deck's, the booked
game's and Fill in's own suites, the notices' landings in `notifications.test.tsx`.

**A feature of its own, because the acts are not the surfaces'.** Members is `groups'`, the record
`player_record`'s, Home's composition the shell's; the five routes, the rule for what a relation
draws (`recordFootOf`, `rowEndOf`), the pill, the record's left button and its two sheets, and the
request cards are this feature's. **Each surface hands its own re-read in** — Members its list, the
record itself — as the record hands `blocks` its re-read: this feature naming those features' keys
while they draw its controls would be a dependency both ways (architecture Part 1). It does import
`proposalKeys`, as `blocks` does, for the faces a friendship moves.

**The relation is the server's, never a guess.** `NONE · SENT · ASKED_YOU · FRIEND`, spelled as the
wire spells it and held equal by `mappers/wireVocabulary.ts`; Members' rows and the record each carry
their own, and nothing here computes one. **Every write settles once the surface has re-read**, so a
pill stays busy until the row under it already says _request sent_, and a sheet's act until the
record no longer needs the sheet.

**Members: the rows keep today's design, and only the end is new** (the README's override 1). Members
draws its row and hands it to `RowWithFriendEnd`, which puts **+ Add** or **Accept** (the `dark`
button in a pill at `sm`, Part 16 2026-11-06) or the _request sent_ (`warn`) or _friend_ (`ok`) tag
on its right, and the write's note under it. **The pill is a sibling of the row's own press**, so a
tap on the face or the name opens the record and only the pill asks — nobody sends a request by
accident. Your own row ends in nothing; the administrator's view draws no end at all. A pill is
spoken with the person's nickname (_Add kuba.w_), since a column of _+ Add_ names nobody.

**The record's foot is one row of two.** `recordFootOf` reads the record: your own draws nothing;
somebody you blocked draws _Unblock_ alone, full width, with no offer to befriend them (the mechanics
§3.5); everybody else draws the friend button on the left beside _Block_ — _Add friend_ (black),
_Request sent ▾_, _Accept_ (coral) or _Friend ✓ ▾_. A record whose blocks could not be read carries
no `blockedByYou`, so the friend button stands alone there, as `blocks`' row is absent. The ✓ and ▾
are `Button`'s new `marks` — Feather glyphs, never characters (Archivo has no ✓; Part 16
2026-11-06).

**The ▾ opens the one action, and the sheet is the confirmation.** The screens §2 draw _a small menu
with the one action_, and #753 puts both _Cancel request_ and _Remove friend_ behind a confirmation.
One sheet does both: its title is the question (_Remove kuba.w as a friend?_), the one act named once
under it, and _Keep_ — `blocks`' confirm sheet, one row over, its close named _Not now_ so two
controls never share a name. A menu of one item followed by a sheet asking about it would be two
presses saying the same thing. Asking and accepting happen on the press: each moves towards somebody
who still answers, or already asked, and a cancel is one sheet away.

**What a friendship moves is every face.** An accept, a crossed request and a removal
(`movesTheFaces`) re-read every group's deck — Fill in and posting with it, under each group's root —
every game still filling and every booked game in detail, and Home: the _friend_ tag is on all of
them. Asking and cancelling move no face and re-read none.

**A refusal that is the state moving is a re-read, and says nothing.** `already_friends`,
`friend_request_already_sent`, `friend_request_not_found` and `concurrent_modification` mean the
surface was drawn from a state that moved — answered on another phone, cancelled by them, two acts
raced. None is retried (asking and accepting are not idempotent, and the global rule retries no
mutation); the surface re-reads, and its next pill is the answer. Any other refusal is said under
the control (`WriteNote`, a second caller of `blocks`' shape kept local until a third): asking
somebody you blocked (`unblock_them_first` — Members still offers **+ Add** on them, since no block
shows on Members, #745's call), and somebody you no longer share a group with. Offline, a write waits
and the amber line says so.

**Home: FRIEND REQUESTS · n above Your games, only while a request waits.** The cards ride on
`GET /home`, which `proposals` reads and maps (`useHomeFriendRequests`); this feature draws and
answers them. One card takes the content width, as friends 5 draws it; two or more are 7.7's peeking
rail. Each card is the face, _ines.d wants to be your friend_, the where-line (_With you in Kazimierz
crew · Padel 3,40 ·_, or _Invited you to Raketa_ for a link's, each part only where the wire named
it) with the reliability chip after it, and **Not now** / **Accept**. Either re-reads Home — and the bell, which the server took the
request's row off (the shell hands `notifications`' re-read in, carried inside the writes since the
card unmounts once Home has re-read) — and stays busy until the card has left on the server's
answer; with the last one the row and its title go.
**Not now is not no** (Q1): the request stays open, and Accept still answers it from Members, the
record or _Asked you_ (#754). **The chip and the record a face opens are `player_record`'s**, so the
shell hands both in rather than this feature importing the one that draws its button.

**Calls made without a ruling, for the product owner to overrule** (all in `friendsCopy.ts`): the
cancel sheet's words (_Cancel your request to kuba.w?_ / _Nobody is told._), since §29 gives only
removing's; the busy words; the two refusal sentences; the spoken names of the pills and the card's
buttons; a Home card whose group either of them left draws its sport and Level alone, and one asked
from a screen with no sport draws the chip alone.

**Not here**: the link (#756), the picker, the friends card and the game (#757–#760).

**Not seen on a device**: the pill and the tags at a row's right on a narrow phone; the record's two
buttons at the narrowest width (#753 asks for that walk); the ✓ ▾ marks beside a label; the request
card and the rail of two; the _friend_ tag across a Fill in square's foot.

## You › Friends, the Add friends sheet, and PLAYED WITH (#754)

**The Friends page is a frame, and its mode is its body.** [#754](https://github.com/Raketa02/Raketa/issues/754)
builds the page from You; [#757](https://github.com/Raketa02/Raketa/issues/757) opens the same page
from a group's Friends tab as a picker (the screens §4). What the two share is the header — back,
_Friends_, **+ Add friends** top right, the black pill friends 3 draws — and the **Add friends** sheet
it opens, so `FriendsPage` is that frame and takes its body (`children`) and its foot (`action`).
From You the body is `FriendsTabs`; #757 hands in the picker and _Done_ without touching the frame.
**No eyebrow**: the header is friends 3's in both modes, so a page shared with a group's court does
not wear the You tab's group title. A pull re-reads every list on it.

**Three tabs, and only _Asked you_ counts.** _Friends · Asked you · You asked_ on the design
system's segmented control; _Asked you · 2_ while requests wait — set-aside ones included, since
**Accept** still answers them (Q1) — and _Asked you_ alone at nought, the count in the label as §29.3
writes it and as the Games switch writes _Competitive · 7_. Each list is the server's, in its order:
friends by nickname (call 11), each with every sport they play and its Level (_Padel 2,75 · Tennis
3,10_); requests newest first. **The rest of every row opens the record**; **Accept** (_Asked you_,
`dark`) and **Cancel** (_You asked_, `secondary`) sit beside that press in the friend pill (Part 16,
2026-11-06) and act on the press, staying busy until their list has read again, so the row leaves on
the server's answer. Cancel asks nothing first, unlike the record's _Request sent ▾_: there it is a
menu of one hiding the act, here the act is named on the row, and a cancelled request can be asked
again from Members. Each tab has a one-line empty state (§29.3's calls), and a failed read says why
with _Try again_.

**Every friends write re-reads this feature's lists.** `friendKeys` names the page's three reads and
the sheet's; `useFriendWrites`' `settle` invalidates them all, beside the surface's own re-read and
the faces. So a request asked on Members opened from the sheet is on _You asked_ back on the page,
an accept on Home is off _Asked you_ and on the You row, and an act on the record a row opened is on
the tab under it when the sheet closes. They are this feature's own keys, so naming them costs no
other feature a dependency.

**The You tab's _Friends_ row closes _Your games_** (a call: the screens say only _a new row_). The
group's rows are who and when a game is with, and a friend is the shortcut to one. Its line is the
page's own two reads, _3 friends · 1 asked you_, and **waits for both** rather than growing a clause
a moment after it is drawn.

**The Add friends sheet: _From your groups_, built for the link card under it.** Each of your groups,
newest joined first, with its tile, its name and _8 members · 2 to add_ (the server's count: not you,
not a friend, no open request either way, nobody you blocked), and a chevron; a tap closes the sheet
and pushes that group's Members, so _back_ is the page. The groups are read when the sheet opens, not
with the page. The sheet's body is a column of sections and the groups are the first; **#756's link
card is the second**, under them. A player in no group reads _You're in no group yet. Join one to add
the people in it._ (a call).

**The tile and the door are `groups'`, handed in by the shell.** The sheet's read names no tile, and
a group's letters are cut once, by the server (ADR-0183 §5), so the tile is drawn off the player's
own Groups list — `groups`' `MyGroupMonogram`, its box held empty until the list is in — and Members
is a `groups` route. `groups` draws this feature's pills on Members, so the shell composes the page
(`YouFriendsScreen`) with both handed in as `GroupDoors`, and with the record a row opens drawn
beside it, as it composes Home's request cards. No navigation hook is used inside the sheet.

**PLAYED WITH, between the score and the star card.** The others on a booked game in Members' rows —
`PersonRow`: the face, the whole nickname, the game's sport over its dot and their Level, without
Members' reliability chip, which the booking does not carry — each handed to `RowWithFriendEnd` for
its pill or tag (the screens §3). A request asked there is `RESULT`'s, naming the game's group and
sport. **Hidden once every one of them is your friend** (`playedWithShown`), and somebody who can no
longer be named is left off first, so a card whose only stranger is a deleted account hides too.
Drawn after a For fun game as after a Competitive one, on every arm of the screen.

**Who builds PLAYED WITH, and who draws it.** The people are the booking's — its seats and its
`played_with` — so `proposals` maps the relations, joins them to the seats (`playedWithOf`) and holds
the record sheet a row opens, with the game's group and sport. The card is this feature's, and this
feature reads `proposals`' keys and Home, so **the result route hands `PlayedWithCard` to
`BookedGameResult`**, which hands the built card to `games`' `GameScreen` through a new `playedWith`
slot, drawn just above _How were they?_. A pill waits for the booking to read again; the record
closing reads it again too. **`proposals` imports nothing of this feature, not even a type** — a
cycle is a defect (architecture Part 1 §6), and the review of #754 caught the type import that first
closed one. It spells the relation itself (`PlayedWithRelation`, held to the wire by its own
`wireVocabulary.ts`) and states what it builds (`PlayedWithInput`); the route passes it to the card,
whose props agree with it structurally, and `tsc` checks the two at that one line.

**One set of read states for every list here** (`ListReading`): offline, the amber line; refused,
the recovery sentence and _Try again_; otherwise the caller's quiet line. The sheet's groups drew
_Reading your groups…_ forever while offline until the review of #754 found it; both now draw the
same three.

**Calls for the product owner** (in `friendsCopy.ts` and the YouScreen note): the You row's place and
line; the sheet's line with no group; the busy and reading words; _Cancel your request to michal.r_
and _Add friends_ as spoken names; the + of _+ Add friends_ typed, as _+ Add_'s is. **The ticket's
example _"Nobody's waiting for an answer."_** is not used: §29.3's three empty lines are.

**Not seen on a device**: the header's pill beside _Friends_ at the narrowest width; the segmented
control with _Asked you · 12_; the sheet's tiles and chevrons; PLAYED WITH's rows with a long
nickname beside _request sent_.
