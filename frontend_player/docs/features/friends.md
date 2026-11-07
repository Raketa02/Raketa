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

**Not here**: the friends card and the game (#757–#760; the card is `proposals`'). The picker is #757's and the link #756's, below.

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

## The link card, and opening somebody's link (#756)

**_Not on Raketa yet?_ is the Add friends sheet's second card**
([#756](https://github.com/Raketa02/Raketa/issues/756); the screens §5; friends 4; the words §29.3):
your link in a recessed field, without its scheme (`linkShown`, _raketa.app/f/tk4m9q2z_), on one
line in mono and cut in the middle so the code stays in view — Info's link card's drawing — with
**Copy** (coral, the card's one action) beside it and a small **New link** under it. The question is
the card's `h2`, inside it, as friends 4 draws it. **Read when the sheet opens**, beside the groups
and in their three read states (`ListReading`); its key is under `friendKeys.all`, so every friends
write reads it again while it is open, which costs one idempotent read.

**The first read makes the link** (#748): the server mints the code then, and two first reads that
race lose one to `concurrent_modification` — so the read retries that once, over the app's own rule
for reads (`shouldRetryQuery`, now exported for exactly this).

**Copy** puts the whole link on the clipboard through the port and says _Link copied_, or that the
phone would not take it — a group page's Copy link's two answers, spelled again here since `groups`
cannot be read back.

**New link asks first**, as #756 asks: a sheet over the sheet — the record's take-back sheets'
shape — _Make a new link?_, what it does to the old one, **New link** and **Keep this link**. The
answer is written into the read (`setQueryData`), the field shows the new link, and the card says
_New link made. The old one no longer works._ (§29.3's call). It is never retried — each one mints a
code — and one that raced (`concurrent_modification`) reads the link again and says nothing, the
friends writes' rule.

**Opening somebody's link is this feature's act; landing is the links feature's**
(`useOpenFriendLink`, the sixth write): this feature re-reads what the answer moved — Home and the
bell (handed in) for `ASKED_YOU`, every face for `FRIEND` — and holds the refusal sentences
(`linkRefused`); how it is retried, when it lands on Home and what it says is
[`links.md`](links.md#a-friend-link-and-the-link-an-android-install-carried-756).

**Calls for the product owner** (in `friendsCopy.ts`): the confirmation's words; _Link copied_ and
_Couldn't copy the link_; the card's title as an `h2` inside the card where the groups wear an
eyebrow above theirs; the blocked owner's sentence; the spoken names.

**Not seen on a device**: the field and **Copy** side by side at the narrowest width, with a long
domain cut in the middle; the confirmation sheet over the Add friends sheet on Android
(`ModalStage`'s layer over a layer); the mint line under the field.

## The picker (#757)

**The page's second body: every friend, a circle each, and Done at the foot.**
[#757](https://github.com/Raketa02/Raketa/issues/757) opens `FriendsPage` from a group's Friends tab
with `FriendsPicker` as its body (the screens §4.2; friends 3, 6). `groups` composes it, as the shell
composes the page from You: the group tiles and Members as the sheet's doors, the picks, and
**Done** pinned in the frame's `action`. No tabs.

**One read for the picker and the court: `useFriendsIn(sport)`**, `GET /friends?sport=`, its own
key under this feature's root so every friends write re-reads it too. Each friend carries that
sport's Level alone, or none, and the list comes **highest Level first, the unrated last** — the
server's order (call 4), never re-sorted. The group's court draws its seated faces off the same
list, so a face is the row it was picked from, and both read a friend's Level by one rule
(`levelIn`).

**A row is one checkbox**: the face, the nickname, _2,75 · established_ (the Level and its band, lower
case, §29.3) in mono, and 6.11's box made round — friends 3's circle — filled `ink` with a drawn tick
when picked (design-system Part 16, 2026-11-07). **Full — three in doubles, one in singles — greys the
rest**, which cannot be picked until one is unpicked, and says _the court is full_ after their name
(a call). A picked row never greys: whoever is seated can be unpicked, a friend who has since lost
their Level included. **A friend with no Level in the sport** is greyed with _No padel level yet_ (§29.3); the
_Ask … to get a padel level_ under it is #758's (below).
**No friends at all** draws the empty state the composer hands in — `groups`' play 55 card.

**The picks are the composer's.** `picked` and `onToggle` are handed in, since Done seats them on
the group's court and the court's line-up is `groups`'; a list read again leaves them where they
were.

**Not seen on a device**: the round box beside a long nickname; the greyed rows (friends 6).

## Asking a friend to get a Level (#758)

**A greyed no-Level row asks: _Ask zofia.b to get a padel level_, and _Asked_ once asked.**
[#758](https://github.com/Raketa02/Raketa/issues/758) (the screens §4.2; the words §29.3; the
mechanics §5) draws the ask under a picker row whose friend has no Level in the sport — the
`secondary` button at `sm` in the friend pills' pill (design-system Part 16, 2026-11-07) — or the
_Asked_ tag where the read's `level_asked_in` names the sport: **once per sport, ever**. `levelAskOf`
is the rule, beside `levelIn`: nothing on a row with a Level, and nothing on a picked row, which is
never greyed. **The words are §29.3's, with no pronoun** (ADR-0096) — _a padel level_, where the PRD
and the ticket wrote _her_ and _their_. **It is a sibling of the row's checkbox, never inside it**,
Members' rule for its pills: the row is shut, and the ask is not, so it is drawn at full strength
under the greyed person, indented to the words.

**The ask is the seventh write, `useAskForALevel`**: `POST /friends/{id}/level-asks` with the
picker's sport and **the group whose Friends tab opened it** — `FriendsPicker` takes `groupId` now —
since that group's picker is what the friend's answer opens for the asker. It settles once this
feature's lists have re-read, so the button stays _Asking…_ until the row already says _Asked_: the
server's answer, never a guess. It moves no face — asked for is not got. **Three refusals are the
state moving, and say nothing** (`stateMoved`): `level_already_asked` (asked from another phone — the
row turns _Asked_), `already_has_a_level` (they got one since — the row turns pickable) and
`friend_not_found` (no longer friends — the row goes). **`not_one_of_your_groups` is said where it was
pressed** — _You're not in this group any more._, a call — and any other failure in its recovery
sentence, through `WriteNote`.

**Where the two notices land is `notifications`'** ([`notifications.md`](notifications.md)): _Level
asked_ the friend's questionnaire through the level pass, _Level got_ this group's picker with the
page on Friends under it. `friendKeys` is exported for it — the friend's Level is what arrived, so the
lists are marked stale as it opens.

**Calls for the product owner** (in `friendsCopy.ts`): _Asking…_; _Asked_ spoken whole, _Asked
zofia.b to get a padel level_; the refusal sentence; _Asked_ as the neutral tag. **Not seen on a
device**: the ask under a greyed row — the indent, a long nickname cutting the pill's one line — and
the tag beside it.
