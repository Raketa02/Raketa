# friends — requests, Members' pills, the record's Add friend, Needs your answer's FRIEND REQUESTS and ASKED FOR A LEVEL

The client side of the backend's **Friends** context: a player asks a group-mate to be friends from
Members or from their record, answers a request on Home, and sees who is a friend on every face.
Built by [#753](https://github.com/Rakieta02/Rakieta/issues/753) for PRD
[#743](https://github.com/Rakieta02/Rakieta/issues/743), on the contract
[#745](https://github.com/Rakieta02/Rakieta/issues/745) built, and decided by
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
crew · Padel 3,40 ·_, or _Invited you to Rakieta_ for a link's, each part only where the wire named
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

**The Friends page is a frame, and its mode is its body.** [#754](https://github.com/Rakieta02/Rakieta/issues/754)
builds the page from You; [#757](https://github.com/Rakieta02/Rakieta/issues/757) opens the same page
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

**_Not on Rakieta yet?_ is the Add friends sheet's second card**
([#756](https://github.com/Rakieta02/Rakieta/issues/756); the screens §5; friends 4; the words §29.3):
your link in a recessed field, without its scheme (`linkShown`, _rakieta.app/f/tk4m9q2z_), on one
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
[#757](https://github.com/Rakieta02/Rakieta/issues/757) opens `FriendsPage` from a group's Friends tab
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

**With one seat, over a booked game** ([#760](https://github.com/Rakieta02/Rakieta/issues/760)):
_Invite a friend_ on a friends game's empty seat opens the same page and picker with `seats` 1, so a
pick greys the rest; the shell composes it around `proposals`' game and order. **`leaveOut` drops the
friends already on the game** before the list is drawn or found empty — the server would refuse each
— and the composer's empty state is drawn when nobody is left.

## Asking a friend to get a Level (#758)

**A greyed no-Level row asks: _Ask zofia.b to get a padel level_, and _Asked_ once asked.**
[#758](https://github.com/Rakieta02/Rakieta/issues/758) (the screens §4.2; the words §29.3; the
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

## A friend's ask for a level, on Home (#765)

**Home: ASKED FOR A LEVEL · n after FRIEND REQUESTS and before Your games, only while an ask waits.**
[#765](https://github.com/Rakieta02/Rakieta/issues/765) (PRD #762; the screens §6.4; the mechanics
§5.1; the words §29.5; Q129) draws the asks the push alone left nowhere to find: **one card per
sport**, the sport with the newest ask first, on `GET /home`'s `level_asks`, which `proposals` reads
and maps (`useHomeLevelAsks`) and this feature draws and answers (`LevelAsksRow`). _n_ is the number
of sports. **It is the request card** — bounded in `ink`, the faces, two lines, **Not now** outline
and the coral button — never the dark _Get your level_, and it **names no group**. The title is
`askersFormOf`'s, a rule of the count keyed in `friendsCopy` so a form with no words fails to compile:
_tomek.k wants to play padel with you_, _tomek.k and kuba.w want…_, and for three or more the two
newest and the rest counted, _tomek.k, kuba.w and 2 more want…_, so it stays one line; the line under
it names the one asker, or says _they_ (ADR-0096). **Up to three faces, overlapping** a third of the
request card's 38 and ringed in the card's white (`groups`' `FaceStack` drawing), the newest at the
back; **each is its own press** and opens that friend's record — the shell hands the record in
(`onFace`), as for the request cards, and one sheet serves both rows. A face behind another keeps
the 26 it shows across, under 6.5's 44: a call, recorded in design-system Part 16.

**The coral button is the _level asked_ notice's act** — `onboarding`'s `useAddASport(FROM_HOME)`:
the sport's questionnaire started, its unfinished run handed back if there is one, a pass of that one
sport begun from Home, so every way out lands on Home. **With a run left halfway in the sport it reads
Carry on**, and the line _You're on question 5._ (`onboarding`'s `useQuestionLeftAt`, off every
unfinished run — `onboardingKeys.runsInProgress`, under `runInProgress` so every start, completion and
abandonment reaches it by prefix — and that run's step, counted as the level door counts it). **The
card draws its start at once and turns to Carry on when the read lands**, unlike the level door,
which waits: here both words are one act, so a press before the read opens the same run. **One
start for the whole row** (`useGetAskedLevel`, over `useAddASport`), and another card's button is
disabled while it is in flight. **A start that fails says the notice's own toast** (`notifications`'
`OPEN_NOTICE_WORDS.unstarted`, handed in by the shell) — _You have a padel level already._ for
`sport_already_rated`, which the hook also reads as the state moving and re-reads Home and the bell,
since the card has gone on the server.

**Not now is the eighth write, `useSetAsideLevelAsks`**: `POST /friends/level-asks/{sport}/set-aside`
sets aside every ask in the sport the card names, telling nobody; then the toast — _You can get your
padel level any time, from You › Skill passport._, neutral and held to be read, carried inside the
write since the card unmounts once Home has re-read — then Home and the bell read again. It stays busy
until Home no longer holds the card. It names none of this feature's lists: an ask set aside moves
nothing they draw. `concurrent_modification` is the state moving — re-read, say nothing.

**For a player rated in nothing the row stands in place of _Get your level_** — `groups`' rule
(`homeAsksForALevel`, which now takes the cards Home's row holds): `HomeLevelCard` draws nothing while
the row holds a card — nor while Home has yet to answer, so the two are never drawn and swapped — and
comes back once the row is empty (`useHomeLevelAsks` is `undefined` only while Home is in flight; a
refused or offline read is none). **A level got ends its
sport's card on the way back**: every level is got inside a pass and every pass ends at the entry
gate, which `useEndOnboardingPass` now tells the sports the ended pass rated; the gate hands them to
the shell's `useRereadAfterALevel`, which drops those sports' cards from Home's cache
(`proposals`' `rereadHomeAfterALevel`, the server's own rule) before the shell draws and re-reads Home
and the bell. Where the push and the bell row open is unchanged.

**Calls for the product owner** (in `friendsCopy.ts`): Not now spoken as _Not now, your padel level_;
_Starting…_ as the coral button's busy word (onboarding's); the overlapping faces' reachable width.
**Not seen on a device**: the card with a long nickname, the faces overlapping, and the toast.

## Strangers from the ranking (#779)

**_Add friend_ on a record opened from Rankings sends the request from the ranking.**
[#779](https://github.com/Rakieta02/Rakieta/issues/779) (PRD #766; the rankings screens §6–§7; the
mechanics §12–§13; the words §30.8). **`AskedWhere` is a union now**: `RANKING` carries the page's
sport, required, and no group — the server refuses one without its sport, and the type says so
before it can. `recordAskedWhere` is the rule every record's request goes through: the ranking, with
the page's sport, where Rankings opened the record; else the record, with the caller's group and
sport. A request from the ranking to a group-mate still names the ranking (call 15).

**The record's foot follows `can_add_friend`** (`recordFootOf`; ADR-0203 §9). _Add friend_ is drawn
only where the record says a request may be sent — they share a group with the reader now, or are
listed on General and not hidden. With nothing between them and no request possible, **_Block_
stands alone** (a call in the screens §6). The other three relations draw their button as before.
**There is no _Unblock_ on the record any more** — a record never opens across a block (#773) — so
the `unblock` foot and the record's `blockedByYou` are gone, and the paragraph above on the record's
foot is superseded by this one.

**The daily limit is said where it was pressed** — `daily_request_limit`, _You've sent 10 requests
to new people today. Try again tomorrow._ (§30.8), in `WriteNote` under _Add friend_, as every
friend refusal is. It is not the state moving, so nothing re-reads and _Add friend_ stays: the
request was not sent. **`unblock_them_first` names You › Blocked players** now (a call): its
sentence pointed at the record's _Unblock_, which is gone, and Members still offers **+ Add** on
somebody you blocked. **`player_not_in_your_groups` says _your groups or on the ranking_**, as the
server widened the code's sentence (#773): a stranger who turned _Show me in General_ off between the
record's read and the press is who meets it now.

**Home's request card reads _Found you in the padel ranking_** for a request made from the ranking —
`proposals` maps the wire's `from_ranking` (`fromRanking`) — in place of the whole where-line, as a
link's _Invited you to Rakieta_ stands, with the reliability chip after it and no sport or Level —
§29.2's group line is the whole line, and §30.8 puts this one in its place. One whose
sport this build cannot name draws the chip alone. The notice's body is the server's words.

**Not on _Asked you_ — a finding for the product owner.** The ticket asks for the ranking line
_wherever a request's origin is named today_ and lists You › Friends' _Asked you_; but its rows name
no origin today (the screens §4.1 draw none, and the row's line is empty), and the wire's
`FriendRequestSchema` carries none — no group, no link, no ranking. Drawing it there would need a
backend field first, so nothing changed there.

**Calls for the product owner** (in `friendsCopy.ts`): the limit sentence under _Add friend_'s half
rather than across both buttons, as §6 of the screens writes it — every friend refusal stands there;
the new `unblock_them_first` and `player_not_in_your_groups` sentences. **Not seen on a device**: the limit sentence wrapping in the left
half at the narrowest width; _Block_ alone across the foot; the ranking line on Home's card.

**No daily limit, and asking somebody no longer askable says nothing** ([#799](https://github.com/Rakieta02/Rakieta/issues/799),
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§2; the words §31.13). Anybody may be asked, as many as you like, so `daily_request_limit` and its
sentence are gone from `FRIENDS_COPY.refused`, and with them #779's call about where the sentence
stood. **`player_not_in_your_groups` became `player_unavailable`** on the server — one code, naming
nothing, for somebody who turned _Show me to new people_ off and shares no group, game or friendship
with the asker — and **it is the state moving** (`useFriendWrites`' `MOVED`): no sentence, the
surface re-reads, and on the record that read is refused with its own one line, _This record isn't
available_, which is the answer ([`player_record.md`](player_record.md)). The old code's sentence is
gone. **The record's foot still follows `can_add_friend`**, which the server now reads off the
relation alone (`NONE` and not your own record): a record that opens is somebody you may ask. The
paragraphs above on the limit sentence and on `player_not_in_your_groups` describe #779 and are
superseded; so is that paragraph's _listed on General and not hidden_.

**The round friend button, and its worded twin** ([#801](https://github.com/Rakieta02/Rakieta/issues/801);
the Home rows mechanics §11, screens §8; Q29; design-system 7.32). `RoundFriendButton` is on every
card of Home's people rows — **+** white, **…** amber, **✓** `mintInk`, the envelope volt with a halo,
each a drawn mark named for whom (`roundLabel`, §31.9's calls) — and `variant="worded"` draws it on a
sheet's title row as _+ Add friend_, _Request sent_, _✓ Friends_, _Accept_ (the comparison and vibe
sheets, #802 and #803; `roundFriendButton.test.tsx` walks it until then). **What a tap does is the
domain's** (`roundPressOf`): **+** asks and the envelope accepts at once; **…** opens _Request sent_ ·
**Cancel request** (no _Keep_: it asks nothing); **✓** opens the record's own _Remove … as a
friend?_. **The next mark is drawn while the write is out** (`shownWhilePressed`), and since every
write settles once the people lists have read again, the read already says what the server did when
the guess gives way — so nothing is written into another feature's cache, and a failed write puts the old mark
back by itself. A refusal that is the state moving says nothing and re-reads (the card leaves on that
read when they turned _Show me to new people_ off); any other is a toast — no room for a note under a
24pt mark. The record's confirm sheet moved to `TakeBackSheet`, shared by both buttons.

**A request found among new players** (#801; the words §31.10). `AskedFrom` gained `NEW_PLAYERS` and
`AskedWhere` a `FoundIn` — a Home row a request was found in, `{ from: 'NEW_PLAYERS' }`, naming
neither a group nor a sport (`toAskRequest` sends neither). **A record a Home row opened keeps the
row** (`recordAskedWhere`'s `foundIn`, ahead of the ranking). Home's request card reads _Found you
among new players_ (`whereLine`'s `newInRakieta`, from `proposals`' `foundBy` since #802) in place of the
whole where-line, as a link's and the ranking's do. #802 and #803 add their rows to `FoundIn`.

**A request found at the same level** (#802; the words §31.10). `AskedFrom` gained `SAME_LEVEL`, and
`FoundIn` its arm `{ from: 'SAME_LEVEL', sport }` — **the card's sport**, the one the other person's
line compares, which the server refuses a request without, so the type carries it (`toAskRequest`
sends it and no group). The card's round button, the comparison sheet's worded one and the record a
face opens all send it. Home's request card reads _Your level in padel · 91% even_ — **today's** %,
which the server works out on the read — or _Found you at your padel level_ once either holds no
level there.

**The request card's origin is one discriminant now** (#802, #801's finding). `proposals`' mapper
folds the wire's four exclusive flags (`by_link`, `from_ranking`, `from_new_players`,
`from_same_level`) into `HomeFriendRequest.foundBy` — `link`, `ranking`, `newInRakieta`, or `sameLevel`
with its %, absent for a group's or a screen's request — and `whereLine` takes the same shape
(`WhereFound`, spelled in `friendsCopy` with each sport already named inside a sentence, so the copy
module imports no feature). `FriendRequestsRow`'s `whereFound` names the sport; a found request whose
sport this build cannot name draws the chip alone, as the ranking's did. A fifth origin (#803's Same
vibe) is one arm in each and a `switch` that fails to compile without its words.

**A request found through the tags** ([#803](https://github.com/Rakieta02/Rakieta/issues/803); the words
§31.10) — that fifth origin. `AskedFrom` gained `SAME_VIBE` and `FoundIn` the arm `{ from: 'SAME_VIBE'
}`, naming **neither a group nor a sport** (`toAskRequest` sends neither, as New in Rakieta's): the
tile's round button, the vibe sheet's worded one and the record the sheet's face opens all send it.
`proposals`' mapper reads the wire's fifth flag, `from_same_vibe`, with `in_common` — **today's** count,
counted on the read — into `foundBy` `{ kind: 'sameVibe', inCommon }`, and the card reads _6 things in
common_, _1 thing in common_, or _Found you through your tags_ at nought. The count's words are
`shared/vocabulary`'s `thingsInCommon`, which the tile and the sheet say too — one spelling for two
features, beside the tag row's own _you too_.

**Every friends write re-reads every read that lists people** (#801; `rereadPeopleLists`, the Home
rows mechanics §13). Home's people rows, their See all and Hottest groups declare `LISTS_PEOPLE`, and
`settle`, `rereadHomeToo` and `rereadIfMoved` re-read whatever did — from any surface, a record Rankings
or a notice opened included. A tag, not their keys: `discovery` draws this feature's button. So
`reread` is now optional on the ask, cancel and remove hooks, and the round button takes none where
its surface is a people list. The request card's three exclusive booleans this paragraph flagged for
#802/#803 were folded into one discriminant by #802 (above).

## FRIEND REQUESTS and ASKED FOR A LEVEL move into Needs your answer (#816)

**Both rows left Home for the sheet the header's envelope opens** ([#816](https://github.com/Rakieta02/Rakieta/issues/816),
PRD #810; [ADR-0205](../../../docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
§1; home refactor 2). They are `FriendRequestsSection` and `LevelAsksSection` now, renamed from
`…Row`, and the shell's `NeedsYourAnswer` holds them, FRIEND REQUESTS first, each drawing nothing
while it holds nothing. What the paragraphs above say about _Home: FRIEND REQUESTS · n above Your
games_ and _ASKED FOR A LEVEL … before Your games_ was true until this one; their reads, writes,
busy rules and re-reads are unchanged.

- **The tile is wider**: the row frame's `wide` rail, `size.requestCardRatio` (0,83) of the content,
  measured off mock 2, the next tile peeking and a lone one at the content width. The ask is drawn as
  the request card (the screens §6.4), so it takes the same width. **Every tile stands as tall as the
  tallest, its title held to two lines and its buttons at its foot**, so the buttons sit level (Q3).
- **A request says who and their chip, and no where-line** (Q2): _With you in Kazimierz crew · Padel
  3,40 ·_, _Invited you to Rakieta_, _Found you in the padel ranking_ and the three Home rows' lines are
  gone, and so is `whereLine` with its words. `proposals` still maps `foundBy`, the group and the one
  sport, since the server still serves them; nothing here draws them. #818 adds the sender's sport
  levels (below).
- **An ask says its title and nothing under it**: _A few questions, and they can add you to a game._
  and _You're on question 5._ are gone; the button still reads **Carry on** for a run left halfway.
- **The coral button's start is the shell's to run.** It navigates, and nothing in a sheet reads the
  navigation (`docs/architecture.md` Part 13), so `useGetAskedLevel` is exported and called beside the
  sheet; `LevelAsksSection` takes `starting` and an `onStart` that closes the sheet for good and
  starts. The _level asked_ notice's toast for a start that fails is the shell's to show, as before.
- **A face still opens the record**, now over the sheet, drawn inside it (`discovery`'s vibe sheet's
  pattern: iOS drops a native window opened while another is closing).

The walks are rewritten: `friends.test.tsx` (_FRIEND REQUESTS in Needs your answer_: behind the
envelope, the tile's words and widths, no where-line, answering, the last answer closing the sheet, a
request arriving while it is open, the record over it) and `levelAsks.test.tsx` (the section, the coral
button closing the sheet and starting, Not now, and _Get your level on Home_ with and without an ask).
**Not seen on a device**: both tiles against mock 2, two lines of title, the buttons level across a
rail of two.

## A friend request names every sport the sender plays (#818)

**The tile reads what the sender plays, under who asks** ([#818](https://github.com/Rakieta02/Rakieta/issues/818),
PRD #810; ADR-0205 §1, §10; Q28): _ines.d wants to be your friend_, then _● Padel 3,40 · ● Tennis
2,90_, then the chip. It is #814's `levels` on each of Home's `friend_requests`, which `proposals`
maps onto `HomeFriendRequest.levels` — every sport the sender holds a published Level in, **in the
order served**, the app's sport order, which nothing here re-sorts. A sport this build cannot name is
dropped, and a server older than #814 sends none, so no line.

- **Each sport is its dot, its name and its Level**, drawn as New in Rakieta's tile draws a sport (a
  `sportDot` before the words), in the muted tiny mono the where-line stood in, tabular as every
  figure. The `·` between two sports is held to the one before it, so a line that wraps ends in one
  rather than starting with one (`sportLevelEntries`, a call).
- **Two lines at most, a sport never split.** The entries wrap whole, and the line is capped at two of
  its own lines, scaled by the phone's text size (`useWindowDimensions().fontScale`), since React
  Native scales a text's line height with its size: a larger text setting draws two larger lines,
  never one and a half. What a third line would hold is not drawn: by the mono's advance, four
  sports should fit two lines on a 393pt phone, and a narrower one may drop the last (an estimate,
  not a measurement). `numberOfLines` cannot do it, as the line is a row of dots and words, not one
  text. A sport too wide for a whole line, at a large text size on a narrow phone, is held to the
  line's width and ends in an ellipsis rather than running past the tile with its Level cut off.
- **No Level, no line**: the title and the chip close up, as before #818.
- **Buttons stay level.** The title, the line and the chip are each held, so the tallest tile has a
  bound, and #816's frame stands every tile as tall as it with the buttons at its foot.
- **Spoken**, who asks and the levels are one element, _ines.d wants to be your friend, Padel 3,40,
  Tennis 2,90_ (`requestTileLabel`, a call), every sport included, those a third line would hold too.
  The face, the chip and the two buttons keep their own names.
- **The request's own `sport` and `level` are still mapped and never drawn**: they are an older app's,
  and `level` is the entry in `levels` for `sport`.

`friends.test.tsx` walks it (_the sport-levels line_): two sports in order, with their dots and mono
figures; the spoken name; no line without a Level; four sports wrapping, held to two lines; and tiles
with no line, one and two side by side, the rail stretching them and each one's buttons at its foot.
The fixtures of every suite that serves Home, a row or a request were brought up to the regenerated
contract (#812–#815's `total`, `needs_your_answer`, `payments_to_confirm` and `levels`).
**Not seen on a device**: the line against mock 2's subtitle, the wrap and the cap on a narrow phone
and at a large text size, the dots' alignment with the mono figures.
