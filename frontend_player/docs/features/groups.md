# groups — Play › Groups, New group, Join a group, and a group's page

> The design record for `src/features/groups/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**Play opens on Groups, and the feature is four screens over six routes**
([#512](https://github.com/Raketa02/Raketa/issues/512), PRD
[#500](https://github.com/Raketa02/Raketa/issues/500), ADR-0182, ADR-0183). The Play tab draws
the shell's _Groups | Explore_ segment
([`shell.md`](shell.md)), and _Groups_ is `GroupsSection`: the groups the player belongs to,
newest joined first, with **+ New** (outlined, `secondary`) and **Join** (coral, `primary`)
above them in every state. **New group**, **Join a group** and **a group's page** are pushed
under `/play/…` — `play/new-group`, `play/join`, `play/group/[groupId]` — so the Play column
stays lit and _back_ is the list. Creating a group **replaces** New group with the group's page,
so _back_ from a new group is the list too, never the form. The words are the mocks' (play 1,
3–13, 23–40), with _Rakieta_ read as Raketa, in `components/groupsPresentation.ts`; the mocks
live in [`docs/specs/play-groups/`](../../../docs/specs/play-groups/README.md).

**Nothing about a group is computed on the phone.** The monogram's two letters and its colour
key are cut by the backend (ADR-0183 §5) — drawn as they come, never re-cased — and the sport
dots, the member count, the distance and every search's order are the server's. The one mapping
on this side is the colour **key** (0–7) to a hue: `MONOGRAM_HUES`, beside `POSTER_HUES` in
`theme.ts` and for the poster's reason outside `theme.color` — a hash-picked hue means nothing,
and a palette that picks by meaning must not carry one. Four of the eight are measured off the
mocks and four chosen between them; white letters clear 4.5:1 on every one
(`monogramHues.test.ts`, design-system 7.20). The tile's letters are set at a share of its side,
as the yes tile's initials are, and shrink to fit at large OS text sizes rather than turning font
scaling off, which Part 13 keeps for the level bar.

**Two rules, pure, in `domain/groupRules.ts`, and the form's one schema.** The New group form
is checked by `schemas/newGroupForm.ts` (_the form + one Zod schema_): `newGroupFrom` answers the
group to create — the name **trimmed**, at most 40 characters, and a home club, which PRD #500
makes required over play 4 — or nothing, and _Create the group_ is pressable exactly when it
answers. `groupAction` — what a row offers: _Join_ on an Anyone group, _Ask to join_ on a People I approve
one, _requested · waiting_ once asked, _you're in_ for a member; a declined request reads `NONE`
on the wire and so quietly comes back as _Ask to join_ (story 43). `searchOutcome` — clubs when a
search found any, otherwise _nothing at that link_ for a `LINK` read and _no match_ for text,
**quoting the text the answer was for** rather than what has been typed since: the search's text
travels on its answer (`ClubSearch.text`) for exactly this.

**Join and Ask to join are one tap on the wire, and the answer decides what the row becomes.**
Both are `POST /groups/{id}/membership`; the answer is the row itself with the reader's new
relation, and `useJoinGroup` writes it into **every cached search that holds that group** — a
club can be in the home-club answer and the join answer at once — so the button turns into its
word without a second read. A join that made the reader a member invalidates the Groups list.
**Neither is optimistic**: whether a tap admits or asks is the group's policy on the server, and
a client that guessed would draw _you're in_ over a group that has just switched to _People I
approve_. A failed join is a `bad` toast, because the row has no line to say it on, and the row
keeps its button; joining twice changes nothing server-side, but the second tap is the player's,
never a retry.

**The two searches are one hook over two routes, asking on every keystroke.** The text, trimmed,
is the query key, so each letter is a new question and the one before it is abandoned through its
`signal`; the answer on screen stays until the next lands (`keepPreviousData`), so the list
narrows under the finger instead of blanking — **except across a blank text**: ✕ cleared the
answer, and Query would otherwise offer the last answer that had data under the next letter, so
the hook remembers the clear and draws no placeholder until a real answer lands. **No debounce** — the ticket asks for every
keystroke, and a cancelled `GET` records nothing. A blank text asks nothing. **Twenty clubs a
page, more on scroll**: an infinite query over `next_page`, and each screen's scroller asks for
the next page within half a screen of its end. The results sit **inside the page's own scroller**
on New group rather than in a list of their own, because a list inside a form is two scrollers
under one thumb. **An answer lives only while it is on screen** (`gcTime: 0`, `staleTime: 0`,
[#529](https://github.com/Raketa02/Raketa/issues/529) D6): it carries the reader's relation to
every group in it, and that changes on another phone — an Owner lets them in, or declines. Kept by
text, the answer to _og_ read before an approval was drawn again the next time _og_ was typed, so
the row flipped between _requested · waiting_ and _you're in_ letter by letter. A text typed again
is asked again; what bridges the letters is only the answer on screen.

**The Groups list is re-read each time the player comes back to it** (`useGroupsList`, #529).
New group, Join a group and a group's page are pushed over it and the stack keeps it mounted, so
_back_ is neither a mount nor a foreground (`useOnReturn`): a reader let in while still on Join a
group came back to the list read before they left, without the group, until a switch to Explore
and back remounted it. The return marks it stale, as the Chats list's does. **A pull reads it again
too** (#529), with the Shell's control and `usePull`, the spinner Info's pull uses.

**New group is the screen's own state and dies with it** (stories 11–27). Every open is empty and
the back arrow discards it. The name field stops at 40 characters (`GROUP_NAME_MAX`); the server
trims and counts again. **The form is three labelled sections on the page and a button, and
nothing else** (the product owner's mocks of 2026-09-27): no card around a section, white fields
on paper, each label over its control at one distance (`FormSection`), and none of the sentences
that explained the form — what a home club is for, the hint under the empty field, the note that
there is no sport to pick, the footnote about the link, and the home club's _· required_, which
the disabled **Create the group** already says. The home club (`HomeClubPicker`) holds no
state and draws five: **empty** (the field alone), **searching** (**a raised card per club** —
name over district · distance · sports and a _Set as home_ pill, the whole head the tap; the
distance is back, the mocks overriding #512, and absent as ever for a reader with no Location
area), **no match** (_No club called "…"_ and that only clubs in Raketa can be one), **a club with
groups** (the same card, its groups on a recessed `paper3` band to the card's edges, each with its
dots, its count, the official mark on an official group, and its action — the player can join from
inside the form, and can still choose the club, because a second group at one club is allowed),
and **chosen** (the field replaced by the club on `mintSoft` with its distance and **Change**, and
nothing under it — the sentence about which courts a game starts with went in the same review). **Each club is its own card with its own shadow** (`shadow.clubResult`, design-system
4.3's one card that casts one) because a club and its groups are one object in a long list, and
dividers between rows could not say where one club's groups ended and the next club began. The
group rows there draw **no approver** — Join a group's still do — and speak what they draw.
_Who can join_ is two chips, _Anyone_ first and chosen. **Create the group** is disabled until the schema answers a group, busy while the create is in flight — two
creates are two groups, and the create is never retried — and on success it seeds the page's read
with the answer, replaces the form with the page and raises _Group created_ in `ok`. A refusal the
form can name (`group_name_invalid`, `home_club_unknown`) is said under the button in the form's
words.

**Join a group is one field and nothing else** (stories 29–44). The field takes the focus as the
screen opens; **Paste** — a chip inside the field, through the new clipboard port — drops a link
from WhatsApp into it, and becomes **✕** while there is text, which clears the text and the
answer. **Each club is New group's club card** (`ClubCard`, the owner's ask of 2026-09-28): raised
off the page, its head on white, its groups on the `paper3` band under it, and the official mark
beside an official group's name, as New group's rows have. The head is **context, not a choice**:
one spoken element with no button role, name over _district · distance · sports_, and no _Set as
home_ pill. Each group row draws its dots, its count and **whether joining needs a yes** on one
line with the action beside it — _11 members · Needs approval_, or _anyone can join_ — the one thing
its row keeps that New group's drops. It named who approves until the owner asked for the shorter
line (#529): whether to ask is what the reader is deciding, and who answers is on the group's page
once they are in. The three ways of
there being nothing are three sentences: _No groups here yet_ on a club's band, _Nothing at that
link_, _No match for "…"_.

**Every failed read is one block** — `ReadFailure`: why, in the caller's words where it can name
the failure (`codeMessage`) and the recovery's otherwise, and _Try again_ **only where the
failure's recovery says trying again can help** — never for `group_not_found`, which answers the
same however often it is asked.

**A group's page opens with its header** (play 40). `ScreenHeader`'s new `compact` form — the
title at `h2` beside the tile in the lead slot, the title and _N members · Home club_ each on one
line and ending in an ellipsis (story 50), spoken whole. An id that is not a UUID redirects to
Play; `group_not_found` — one code for _no such group_ and _not one of yours_ — is one sentence.

**Two things the mocks draw that this record departs from, and why.** The mocks draw the sport
dots on a card with **no sport name beside them**, which design-system 2.3's premise says a dot
always has: they are drawn as the mocks draw them, and **every element they sit in speaks the
sports by name** (_…, plays Padel, Tennis_), so a listener gets the words — a reader who cannot
tell the four hues apart still gets them only from the group's page. Recorded in design-system
Part 16 for the product owner to rule on. The home-club field's focus ring was **coral**, as #512
asked, until the 2026-09-27 mocks drew it `ink` like every other field. **Nothing here has been
seen on a device.**

**The page is filtered by one sport, and the phone remembers which**
([#513](https://github.com/Raketa02/Raketa/issues/513), stories 51–58, ADR-0188). The fast
filter lists **only the sports the reader is rated in**, in the registry's order — never the
group's dots, since a player may be the only one here who plays a sport and a dot they are not
rated in is a sport they cannot play — and a player rated in one sport gets a **plain label** with
nothing to unfold. It opens on **the sport last picked in any group's filter**, the store's
`lastSport`, judged against the ratings on every read (`domain/groupPage.ts`' `openingSport`): a
sport no longer rated, or a value that was never a sport, is the first rated sport in the order
padel › tennis › squash › badminton. **Nothing is drawn for a sport until the phone has answered**
— the pill and the tabs' bodies wait for both reads — so a page never draws one sport and jumps to
another. The read and the write are `usePlaySegment`'s shape (`useGroupSport`): local, never
waiting on the network, a pick written to the cache and then the phone, never a mutation.

**The filter unfolds on the UI thread and folds at once** (play 41–42; design-system 7.21). The
pill is a chip; tapped, a white bar with the popover's shadow grows leftwards over the group's
name from where the pill stood, the current sport dark at its right end, the others sliding out
one by one — one Reanimated shared value over `motion.unfold`, read by the bar's width and each
sport's opacity and slide, never a scale. It is the second surface on Reanimated after the radar
and the first with no gesture. The bar is drawn over the header's measured box, above a backdrop
across the page, so **a tap on another sport picks it, and a tap on the current one, anywhere else,
or Android's back folds it and changes nothing.** The shell's tab bar is outside the page and
stays live, so leaving by it folds the bar too, and a page the player comes back to is never
open. It is never a `Modal` (ADR-0178). The fold is immediate; under reduced motion the bar is simply open. `sportFilter.test.tsx` holds the width at
each end of the unfold and under reduced motion, with the layout handed in as events.

**Open, the bar never ends across the group's tile** (#529 E2). With every sport in it, the bar
stopped a few points into the tile and a sliver of the tile showed past its round end. The header
hands the tile to `SportFilterPage`'s `cover`, which measures it, and the bar is told two widths: the
one at which it reaches the tile, and the one that covers it whole with `space.xs` to spare — short
of the back arrow, which stands a `space.sm` gap before the tile. Sports that would end across the
tile open the bar that far; sports that stop short of it end the bar where they do. Members has no
tile and covers nothing.

**Four tabs, no counts, and the page always opens on Games** (story 59; ADR-0188 §5 keeps which
tab nowhere). Games, Fill in and Friends are each drawn for the filter's sport; Info is
[#514](https://github.com/Raketa02/Raketa/issues/514)'s, below. **Every starting
tab has one dark card whose remedy is the link** (`LinkCard`): a headline, what the app is waiting
for, and **Share the link** (volt) beside **Copy link** (`onDark`). Share hands the phone's own
sheet one sentence — _Join my raketa group on Raketa: <link>_, the administrator's WhatsApp words
(story 128) — through the new **share port**; closing the sheet is an answer, never an error. Copy
puts the bare link on the clipboard, which learned to write (`writeText`), and says _Link copied_
in `ok`, or _Couldn't copy the link_ in `bad`, so a tap never passes silently.

**Games reads the group's per-sport roster, and says only what it can** (stories 60–63, ADR-0183
§13). `GET /groups/{id}` serves `rated_by_sport` — every sport's count of members rated in it and
the first of them in joining order, at most a court's worth — and `gamesCard` turns it into three
states against the court's seat count (handed in: `courtSeatCount` is drawn knowledge): **Just you
so far** while nobody else is rated in the sport; **N of M** once others are, their faces in the
order they joined; **Nothing picked right now** once the seats could be filled — and then **no
waiting line**, because what the app would wait for is not people. The row of seats is one element
to a listener, play's court summary — _Padel, 1 of 4 seats filled._ — and _3 of 4_ is drawn in
mono, as every count is (design-system 1.4).

**Fill in counts members, not players of the sport** (stories 66–67). _No games yet — it's just
you_ while the reader is the only member, _No games yet_ once anybody has joined: a posted game is
seen by everybody who arrives with the link. **+ Post a game** is the primary button over the page's
bottom corner — drawn disabled until posting shipped, and since #558 the door to _Post a game_
(below).

**Friends is a court with nobody to put on it yet** (stories 68–70; PRD #500 overrides play 49–56:
no friends feature). **Competitive · For fun** is a process-scoped store (`gameIntent.store`) —
it keeps its position when the player leaves the page and comes back, and ADR-0188 §5 keeps it off
the phone; one value for the app, since it is the intent of the game being built. Like the app's
other process stores, a sign-out does not reset it.

**The court is the app's court, spoken in the seat's sentences.** `Court` at `court.build` with
`shared/ui`'s `SeatFace` and `SeatCaption` — Play's until #574, and drawn by Fill in and a booked
game's players card too — and the reader in the first seat, captioned _You 2,71_; every other seat is a dashed ring with a
white plus that opens **Friends**, as **+ Friends** does. Who sits on which side is the seat's rule
(`seatPlaces`, a side is a team, so squash's other seat is _their side_) and every seat says so in
the seat's sentences (`shared/vocabulary`'s, #574): _Padel, 1 of 4 seats filled._ first, then _Your side, you, level 2,71_, _Your
side, your partner, empty_, _Their side, empty_. The Games card's row speaks the same summary.
**Side labels are drawn on padel and badminton only**, as the mocks draw them: squash has no
halves, and tennis's far seat stands where the label would be written.

**The reader's face is the roster's, and their own record's only when it must be.** The group's
read carries the first rated in each sport, which is the reader in nearly every group; one who
joined after a court's worth gets their photograph from their own record (`player_record`'s
`useOwnFace`, a read asked only then), and the poster until it answers.

**The Friends screen** is pushed at `/play/group/[groupId]/friends?sport=…` — the sport is a
validated route param because the eyebrow counts that court: _PADEL · 0 OF 3 PICKED_ — and always
shows _Nobody you know here yet_ with the link's doors. The page's route moved to
`[groupId]/index` to make room for it.

**Three things the group page's mocks draw that this record departs from**
([#513](https://github.com/Raketa02/Raketa/issues/513), design-system Part 16). The Games card's
faces are **the face box, not circles** — this app has no round face (#338) — and **no face carries
initials**, which ADR-0167 §3 fences to the yes screen's tile; widening that fence is an amendment
to the ADR, not a drawing call. **+ Post a game** is **the primary button at 4.2's corner** rather
than the mocks' coral pill with a glow: the pill is the chip's and the yes screen's, the glow the
⚡Play disc's (disabled until #558 opened it). All three are flagged for the product owner. **Nothing on the page has
been seen on a device** — the unfold's pace, and whether four sports fit the bar on a 320pt phone,
are asked for a look.

**Info is the group rather than a sport of it** ([#514](https://github.com/Raketa02/Raketa/issues/514),
stories 71–79; play 57–60, club 20). Top to bottom: **the link card** — the link in mono on one line,
cut in the middle so its code stays in view, and **Share** and **Copy** beside it, drawn short and
spoken whole (_Share the link_, _Copy link_), the same two doors as every other dark card on the page;
**Want to join · N**, the Owner's; **the members row**; and **Edit group**, the Owner's. **The way
out stands at the page's foot**, under what scrolls rather than in it (#529 F1), so it is in the same
place however long the queue above it grows; the group page draws it, because the page owns the
scroll. Info never waits for the filter's sport, because nothing on it is drawn for one.

**The Info tab counts the requests waiting on an Owner, and Info re-reads on a pull**
([#529](https://github.com/Raketa02/Raketa/issues/529) D6). The count is the Chats badge at the
segment's size (`Segment`'s `badge`, `size.segmentBadge`) over the tab's top-right corner, drawn from
every tab and spoken with the tab's name (_Info, 2 requests waiting_), so an Owner on Games knows
somebody is asking. It reads the Owner's requests under the same key as _Want to join_, so the page
now asks for them as it opens rather than when Info is opened, and an answer that takes a row takes
it off the count in the same frame. Nobody but the Owner reads the requests, so nobody else's tab
carries a count. **A pull on Info** re-reads the group and everything read under it that is on
screen — who is waiting, the members row, the count — and the other three tabs, which are drawn for
a sport, keep no pull. **So does coming back to Info** (#529 F2): from another tab, and from a screen
pushed over the page (Members, Edit group, by `useOnReturn`), so what another phone changed meanwhile
is on it without a pull. The first look at Info re-reads what the page asked for as it opened; that
is one more read of the group and the requests, paid on a tap.

**The members row is the server's faces and the phone's arithmetic** (`domain/groupInfo.ts`'
`membersRow`). The group's read serves up to five faces of everybody but the reader in Members' order
— the Owner, then newest joined first — with a blocked pair left out; the row stacks them, each ringed
in the card's white, and _+N_ counts the other members it does not draw, `member_count − 1 − faces`.
With no face served the reader's own stands in, off the roster the page already holds (`readerFace`):
alone, that is play 57; hidden from everybody by a block, it is still a face, and _+N_ counts the
rest. The line under _N members_ is the dots and who approves: _anyone can join_, _you approve joins_
to an Owner, _the owner approves joins_ to anybody else — the group's read names no Owner, so a member
reads _the owner_, as a search row whose Owner can no longer be named does. The whole row is one
element, spoken with the sports by name, and it opens Members.

**Want to join is club 20's card, and an answer takes its row at once.** Asked only while the reader
owns the group — anybody else would be refused, and a read that can only be refused is not asked —
and drawn only while somebody is waiting, and not while the queue is being read, so the members row
never drops a card's height and comes back. Each row is the face, the whole Name and, under it,
**the first two sports the person is rated in** — the sport's dot, its short name and the Level in
mono (_● Pad 2,44_) — **and one _+N_ for the rest**, in the order served (#529, the owner's mock of
2026-09-30: four sports in full ran the row onto three lines). **No tag around either** (the owner's
ask, 2026-10-01): the dot and the text, `space.sm` between sports, and the count as text alone. The
row is still spoken with every sport by its whole name. **✕** is _Decline {name}_ and **Approve** _Approve {name}_. **This write is optimistic where a join is not** (`useAnswerRequest`): either answer ends the
request whatever the server then does, so there is nothing for it to decide about where the row goes,
only whether the tap reached it — the row goes on the tap and comes back, with a toast in the Owner's
words, only on a refusal — that row alone, where it stood, since another answer may still be on its
way. The queue is re-read once the last answer in flight has landed, never after
each, which would draw a row answered a moment ago back in. An approval re-reads the group, its
Members and the Groups list: every count moves by one. The refusal's words are handed into the hook
by the section rather than said by the row, because the row is gone by the time a refusal lands.

**Edit group is New group's Name and Who can join, in cards, and the You tab's Save**
(`EditGroupScreen`, pushed at `/play/group/[groupId]/edit`). _Name_ and _Who can join_ are
`GroupFormCards`, drawn for both forms, and the name is one Zod rule for both (`GroupNameSchema`).
**Save** reads _Saved_, settled, while the form says what the group says (`detailsUnchanged`), so a
save that would record nothing is never sent; the screen stays after a save, as the You tab's do, and
the answer is written under the page's key, so _back_ lands on the new name. _Who can join_ carries no
note here (#529): the Owner is past choosing what the group is. **A save that switches People I
approve to Anyone is asked first** (#529) — a sheet, _Let anyone join?_, saying _Selecting Anyone
allows anyone to join the group, including players with pending requests._, whose _Save_ sends it;
its close, _Keep People I approve_, sends nothing and leaves the form as it was. **A switch to Anyone
shows who it let in** — _LET IN · N_, a face and a name each, in the order they asked, off the answer's
`admitted` — and re-reads the requests and Members, which the switch emptied and grew. A refusal the
form can name is said under Save; `block_state_unavailable` records nothing, so the next Save is the
whole edit again.

**The way out is one door and a sheet** (`ExitDoor`). _Delete the group_ for an Owner who is the only
member, _Leave the group_ for everybody else — an Owner with others included (`groupExit`). The sheet
is the departure's shape: a title naming the moment, a close named by what it keeps, focus on the
title, and the act named once. It says what leaving does before it happens — an Owner's group passes
to whoever has been in it longest, with the requests waiting — and how to come back under the
group's rule. **The sheet is the surface while the act is in flight**: it stays up, its act busy, and
says a refusal in words. `lone_owner_cannot_leave` and `group_has_other_members` mean the count moved
since the page was read; the group is re-read, and the sheet's act becomes the door that works.
Success is a `dismissTo` the Groups list, the card already dropped from it, and a toast. **What is
read about the group is marked stale and not re-read**: the page is still on its way out, and a
re-read would draw _not one of yours_ over it as it leaves. **Closing the sheet takes the act back,
even one the network is holding** (`useExitGroup`'s `takeBack`, #529 F5): offline, a leave waits for
the connection, and a paused mutation outlives the sheet that started it — `reset` only lets go of
it — so a leave the player closed the sheet on went out on the next reconnect, from whatever page
they were on by then. The waiting act is removed from the queue with the close; one whose sheet is
left open still goes when the phone is back.

**Members is the server's list for the filter's sport** (play 61, stories 80–84; `MembersScreen`,
pushed at `/play/group/[groupId]/members`). The header is **_Members · N_**, N the rows the list
draws for the pill's sport — it moves when the sport does, read off the list's own query, and is the
word alone until the list is in or where there is no sport to list (2026-10-01: the _PLAY PADEL · N_
heading over the list gave its count to the title and went). No eyebrow — the group's name and count
over it said nothing the page it was pushed from had not (#529) — and **the same pill as the page,
over the same state**:
the filter is now `SportFilterPage`, the header, the body and the unfolding bar the page and Members
share, and the sport is `useGroupSport`'s one value, so a pick on Members is the page's sport when the
player goes back. The rows come in the server's order — the
reader as _You_, the Owner with a `base` **admin** tag, then newest joined first. **The Player Score
is a tag beside the name** (2026-10-01, the product owner's mocks): `PlayerScoreTag`, a drawn ✦ and
the figure in `num.tag` on the tint of `scoreBand`'s band — mint 90–100 (the best partners), neutral
70–89 (nothing to flag; 70 is the matcher's `SCORE_MIN`), amber 50–69 (worth a look before approving
or inviting), red 0–49 (risky) — then the admin tag. Under the name, the **sport's dot** and _Padel
2,71_. **No tag where there is no record**, never _score 0_. The row is spoken as drawn: _Karol
Tomczak, score 93, admin, Padel 2,75_ — the figure, not the band, which is a reading of it. The mocks
typed the strong band in `mint` and the amber one in amber's retired `#9A6A0B`; both fall short of
4,5:1 on their tints at 9,5pt, so the tag draws `mintInk` and today's `amber` (`PlayerScoreTag.test`).
**No friend tag**: PRD #500 overrides play 61 by name, and the 2026-10-01 mocks' _friend_ with it.

**Members opens the record on a tap** (2026-10-01, the product owner's ask). It was a press and
hold, as #514 and play 61 asked, with the row's standard `longpress` accessibility action and a page
footer, _Press and hold anyone for the full record._, to explain a gesture with no affordance. A tap
is the obvious gesture and answers #285's objection to the hold the way the games feature's players
card does: the row is a button, every screen reader activates it, and its hint says what it opens
(_Opens their record_, _Opens your record_). The footer and the custom action went with the hold. It
opens the existing `PlayerRecordSheet` with the filter's sport; the reader's own row opens their own
record.
**Everybody on the list can be opened** because a group both are in is a disclosure the record
route admits on (ADR-0159's 2026-09-30 amendment); before it, anybody the reader had not been shown
by a search, a challenge or a game met _This record isn't available_ (#529 F1).

**An official group's Administrator opens the same Members** (#529, the product owner's ask) — from
the members card on the group's page in the administrator area, at
`/administrator/[clubId]/group/[groupId]/members` (`AdministeredMembersScreen`). The header, the
rows, the tags and the record sheet are this screen's; two things differ, because running a group
is not playing in it. **The pill lists the sports the group declares** (`useDeclaredSport`), not the
ones the reader is rated in, so an Administrator who plays nothing sees the list rather than an
_Add Padel_ card, and **a pick is held while the screen is up and kept nowhere** — Play's last sport
is the player's choice. The group's sports come from the administrator area's read, handed in. To
make that possible the filter's page split in two: `SportFilterPage` reads `useGroupSport` and draws
`SportFilterFrame`, which takes the filter's state from whoever holds it. **The server admits whoever
runs an official group** to the members read and to its members' records, as a member is admitted
([#566](https://github.com/Raketa02/Raketa/issues/566)). **A refused list
says why in its caller's words** (`refused`, by code): a member's _This group isn't one of yours._,
the page's own, and the Administrator's _This isn't a group you run any more._ — where it had fallen
through to the recovery's _Something went wrong at our end_, which blamed the server for a refusal.

**Members always says who runs the group** (#529, the product owner's ask, 2026-10-02). A member
could not find who runs an official group: its Administrator need not play in it, so was on no
list, where a player group's Owner is a member and leads it. Knowing who answers for the group —
who approves joins, who to go to — is worth having at any moment, so **a card over the list names
them** (`RunnerCard`, `runnerApart`): the club's tile (`ClubTile`, the administrator profile's own
face, lent from here since), their whole Name and the **admin** tag, over _runs this group for
Ogrody 33_ in Info's lower-case line; and while the group **needs an administrator**, the club over
_no administrator right now_. **Nobody is drawn twice**: the card is left out wherever the sport's
list carries the Administrator's own admin-tagged row, which says it better, and for a reader who
runs the group. It is one element spoken as drawn, **not a button** — an Administrator need not play,
so there may be no record, and the group's read carries a name and no id — and **not a member**, so
_Members · N_ leaves it out. It is drawn once the list is in, so a runner whose row is on it never
flashes first. Nothing new crosses the wire: the read has carried the name since #510. **Two calls
are the product owner's:** the card names the Administrator to a member who has a block with them,
whose row the list hides — who runs the group is the group's fact, not a partner listed, and the
server sends the name either way; and **a player group's Owner is still not named on a sport they
are not rated in**, where they are on no list — closing that needs the Owner's name on the group's
read, a backend change. **Not yet seen on a device.**

**What this record departs from, and what is open.** The way out is 6.1's `secondary` where play
57–60 draw it in dark red: `red` is _ended badly_ and coral is closed at six. Club 20 draws the
Levels in sans; they are mono, as every Level is. Both are in design-system Part 16 for the product
owner, with the stacked faces' sizes. Leave, Delete, Save and the two answers pause offline and resume, as join and
create do; no act here says so beside itself yet. **Nothing here has been seen on a device.**

**The administrator area draws with this feature's pieces, and they are lent from `types.ts`**
([#516](https://github.com/Raketa02/Raketa/issues/516); [`administrator.md`](administrator.md)). An
official group is a Group, so the tile, the dots, the group forms' two cards, the request row, a
failed read, the row face, the stacked faces and the words they share are exported for that one
caller, and the dependency points one way. Four changes made the lending possible without changing
what this feature draws: **the members row's faces left `InfoTab`** for `FaceStack`, which the members
card on an official group's page draws too; **the request row left `WantToJoin`** for `RequestRow`,
which answers nothing itself — the two taps are props, so an Owner's queue and an Administrator's each
answer through their own routes, as #514's handover suggested; **_Who can join_ can be drawn without its _no sport to pick_ note**
(`noSportNote`), which is false of an official group; and **the Name card takes a placeholder and an
error**, for _Same name as the WhatsApp group_ and a refusal said on the field. The share sentence is
the administrator's WhatsApp post too, as #513 already wrote it for. **Edit group's _LET IN · N_ card left the
screen** for `AdmittedCard` ([#517](https://github.com/Raketa02/Raketa/issues/517)), which an official
group's settings draw after the same switch to Anyone. **Edit group's _Let anyone join?_ sheet left
the screen** for `OpenToAnyoneSheet` (#529, 2026-10-02), which an official group's settings open
before the same switch, so an Administrator is asked in an Owner's words.

**An official group is a Group the player meets as one, told apart by what it plays and who
answers** ([#519](https://github.com/Raketa02/Raketa/issues/519), PRD #500 stories 40, 56, 57;
ADR-0183 §3, §6, §7). The reads carry `kind`, and nothing else about the drawing changes: **its
dots are its declared sports**, served as `sports` on every row, card and page — the Groups list,
both searches and Info's members row; the header draws no dots (play 40), so "the group header" in
the ticket is the page's. **Whether it needs a yes** is the row's line in Join a group
(`approverLine`): since #529 _Needs approval_ whoever answers — its Administrator, or the club while the group
**needs an administrator** (`administrator_name` null) — and _anyone can join_ on an Anyone group of
either kind. Info's line reads _the
administrator approves joins_, as a member reads _the owner_ on a player group. The group's read
names nobody at #519; it has carried `administrator_name` and `is_administrator` since #510, and
`Group` maps them for Members' who-runs-it (#529, below) — Info's line still says _the
administrator_.

**Its name carries the official mark** (`OfficialMark`, #529): in both searches, where the
2026-09-27 mocks drew an _official_ tag, and beside the name in its page's header. A twelve-point
seal in `mintInk` with `Tick`'s own path in white, **no bigger than a lowercase letter** — its box
is Archivo's x-height as a share of the name's font size (`size.officialMark`), 6,84pt in a row
and 7,89 in the header — on the name's line and centred on it. The mark is hidden from a screen
reader and the word moved into the spoken name: the row's _Ogrody 33 Club, official, …_ as before,
and the header's `titleLabel`, _Ogrody 33 Club, official, 12 members · Ogrody 33_. **The Groups
list's card carries it too** (2026-10-01, the product owner's ask): beside the card's `h2` name,
7,89pt, and the card's spoken name says _official_ after the name, as the row's does. The list's
read already served `kind`; `MyGroup` carries it now.

**An account that runs an official group joins it directly** (`groupAction`): the row it runs is
**Join** whatever the policy, in both searches and New group's club rows, and the one tap admits it.
That outranks _requested · waiting_ too — a request left before the club made them its
administrator is admitted by their own Join (#509) — so only _you're in_ outranks it. Members'
**admin** tag goes on a player group's Owner or an official group's Administrator who joined as a
player (`adminTagged`); the server orders them second, as it does an Owner.

**The fast filter narrows to what the group plays.** `useGroupSport` and `SportFilterPage` are
handed the group's `declaredSports` (absent on a player group), so the filter lists the sports the
reader is rated in **among them** and opens on one of them whatever was picked elsewhere; opening is
not picking, so the phone keeps what the player last picked. **A member rated in none of them**
gets `AddSportCard` — _This group plays padel_ / _Add padel to your Skill passport to see its games._
— in place of Games, Fill in and Friends, and of Members' list, with no pill and no _+ Post a game_.
**Info is drawn as ever**, because the way out is not a sport's: a member who cannot play a group's
sports must still be able to leave it. Each of its buttons, one per sport the group plays, is the
Skill passport's _Add a sport_ for that sport (`useAddASport`), so the questionnaire is onboarding's
and the pass ends where every pass begun there does — on the passport, not back on the group. A
declared list this build can name none of — an older build after a sport is added — is carried as
none (`toGroup`), so the page reads the group as a player group's rather than drawing nothing.

**Calls made here, open for the product owner** (design-system Part 16 has the card's): the whole
name on the approver line; Info's _the administrator approves joins_; the card on the three tabs
rather than in place of the tab bar, and on Members; a button per sport, with the sports joined
_padel and squash_ / _padel or squash_; the pass ending on the passport; and Join over a request
left before the account ran the group. **Nothing here has been seen on a device.**

**Join a group opens with a group link in its field** (#520, story 46). A link tapped in WhatsApp
reaches the screen with its code (`/play/join?code=`, `parseJoinRouteParams` over `GroupCodeSchema` —
eight letters and digits, read lower case, the shape the links feature reads a link's code with too), and
the route file spells the group's link back from it (`appLinkTo`: the scheme's while no domain is set)
for the screen's field, so the answer is exactly the group a paste would have found. **The field does not take the focus then**:
there is nothing to type, and a keyboard over the one result would hide the button the link is for. What
opens the screen, and when, is [`links.md`](links.md)'s.

**`find_a_game` became `classic_play`** ([#550](https://github.com/Raketa02/Raketa/issues/550)),
and then went with the old loop ([#576](https://github.com/Raketa02/Raketa/issues/576)). Nothing
here changed either time: Play opens on Groups, and no flag decides it any more.

**Games is the deck** ([#553](https://github.com/Raketa02/Raketa/issues/553), the screens A1–A2).
`GamesTab` hands `proposals`' `GamesDeck` the kind the page's switch stands on — the game-intent
store, which Friends' switch shares, so one choice is one choice on both tabs — and the starting card
to draw while the segment deals nothing. **The starting card is unchanged** (_Just you so far_, _3 of
4_, _Nothing picked right now_), and _Nothing picked right now_ gains a third door under the link's
two, _Post a game_ — Fill in's own `PostAGame`, in `LinkCard`'s `foot`, open since #558. **The tab bar counts Games** — the cards somebody is already In on with you, off
the same deck read the tab draws (`useGamesBadge`), in the Info badge's mark and spoken _Games, 4 with
somebody In_; and Fill in counts its _Seats to fill_ (below). **Games lays itself out**:
the deck fills the page between its switch and its three buttons, so `GroupScreen` draws it outside
the page's scroller, and the deck scrolls itself in the states that are not a deck. Every suite that
opens a group's page stubs the deck (`test-support/groupDeck`'s quiet deck); the tab's own walk is
`groupGames.test.tsx`. The record of the deck itself is [`proposals.md`](proposals.md).

**Fill in is `proposals`' board** ([#557](https://github.com/Raketa02/Raketa/issues/557), the screens
A1, A3; mocks 11–14). `GroupScreen` draws `FillInBoard` as the tab — _Seats to fill_, the rescues the
reader is offered, then _You're In_, their own yeses on this group's games still filling — and hands
it the starting card above (`FillInTab`) for a tab with no row in either, as `GamesTab` hands the deck
its own. **The tab bar counts Fill in** — the _Seats to fill_ rows, the board read's own `badge`
(`useFillInBadge`), spoken _Fill in, 1 seat to fill_ — read for the page's sport whichever tab is
open, so `stubGroupDeck` now serves an empty Fill in too and every suite that opens a page gets it.
**+ Post a game** floats over the page's corner on Fill in; the board leaves room under its last row
for it. The tab's walk is `groupFillIn.test.tsx`; the board's record is [`proposals.md`](proposals.md).

**_Post a game_ is `proposals`' screen over the page** ([#558](https://github.com/Raketa02/Raketa/issues/558),
the screens A5). Both doors — Fill in's floating button and _Nothing picked right now_'s third — push
`/play/group/[groupId]/post`, whose route mounts `PostAGamePage`: it hands the screen the page's own
sport filter (`useGroupSport`), each sport's rated count off the group's roster, the page's sport and
the switch's kind; a reader rated in none of an official group's sports gets `AddSportCard` with _Get
rated in padel to post here_ (Q80). **Which tab the page is on is now a store** (`groupTab.store`)
rather than its state: _Post a game_ turns the page to Fill in **as it opens**, unseen under it, so
the chevron, the hardware back and the swipe all land on _You're In_, as A5 asks whichever door was
used. The page forgets its entry — and the post's draft (`forgetPostDraft`) — when it goes, so it
still always opens on Games (story 51, ADR-0188 §5). The record of the screen is
[`proposals.md`](proposals.md); its walk `proposals/components/postAGame.test.tsx`.

**A group's page opens at a card when a notice says so** ([#559](https://github.com/Raketa02/Raketa/issues/559);
the screens A9: _the deck opens with the card on top_). The route reads an **arrival** beside the
group's id — the card's sport, kind and id, all three or none (`parseGroupRouteParams`), spelled by
`groupDeckRoute`, which `notifications` pushes. The page stands on the card's sport until the player
picks another (`useGroupSport`'s `opening`, `openingSport`'s `wanted`) — **opening is not picking**, so
the phone's last sport is untouched — turns to Games, moves the switch to the card's kind
(`gameIntent.store`, one value for the app), and hands the card to the deck as `onTop`. An arrival
this build cannot read opens the page as it always opens: the group's id alone is a page.
