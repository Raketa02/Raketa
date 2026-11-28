# groups — Play › Groups, New group, Join a group, and a group's page

> The design record for `src/features/groups/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**Play opens on Groups, and the feature is four screens over six routes**
([#512](https://github.com/Rakieta02/Rakieta/issues/512), PRD
[#500](https://github.com/Rakieta02/Rakieta/issues/500), ADR-0182, ADR-0183). The Play tab draws
the shell's _Groups | Explore_ segment
([`shell.md`](shell.md)), and _Groups_ is `GroupsSection`: the groups the player belongs to,
newest joined first, with **+ New** (outlined, `secondary`) and **Join** (coral, `primary`)
above them in every state. **New group**, **Join a group** and **a group's page** are pushed
under `/play/…` — `play/new-group`, `play/join`, `play/group/[groupId]` — so the Play column
stays lit and _back_ is the list. Creating a group **replaces** New group with the group's page,
so _back_ from a new group is the list too, never the form. The words are the mocks' (play 1,
3–13, 23–40), with _Rakieta_ read as written (ADR-0211), in `components/groupsPresentation.ts`;
the mocks live in [`docs/specs/play-groups/`](../../../docs/specs/play-groups/README.md).

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
[#529](https://github.com/Rakieta02/Rakieta/issues/529) D6): it carries the reader's relation to
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
area), **no match** (_No club called "…"_ and that only clubs in Rakieta can be one), **a club with
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
([#513](https://github.com/Rakieta02/Rakieta/issues/513), stories 51–58, ADR-0188). The fast
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
one by one — one Reanimated shared value over `motion.unfold`, read by transforms and opacity
only, never a scale and never the bar's width: the bar is laid out once at the pill's width and its
far half slides out from under the current sport, because a width animated frame by frame went
through Reanimated 3.16's shadow-tree commit and held still while React committed (2026-11-24,
`SportPill`'s note). It is the second surface on Reanimated after the radar
and the first with no gesture. The bar is drawn over the header's measured box, above a backdrop
across the page, so **a tap on another sport picks it, and a tap on the current one, anywhere else,
or Android's back folds it and changes nothing.** The shell's tab bar is outside the page and
stays live, so leaving by it folds the bar too, and a page the player comes back to is never
open. It is never a `Modal` (ADR-0178). The fold is immediate; under reduced motion the bar is simply open. `shared/ui`'s `SportPill.test.tsx` holds the width at
each end of the unfold and under reduced motion, with the layout handed in as events.

**Open, the bar never ends across the group's tile** (#529 E2). With every sport in it, the bar
stopped a few points into the tile and a sliver of the tile showed past its round end. The header
hands the tile to `cover`, which `SportPillFrame` measures (#774), and the bar is told two widths: the
one at which it reaches the tile, and the one that covers it whole with `space.xs` to spare — short
of the back arrow, which stands a `space.sm` gap before the tile. Sports that would end across the
tile open the bar that far; sports that stop short of it end the bar where they do. Members has no
tile and covers nothing.

**The pill is shared UI's, and the filter is the page's**
([#774](https://github.com/Rakieta02/Rakieta/issues/774)). Rankings draws the very same control, so the
pill, the bar and the layer they open on — the backdrop, the header's measured box, folding on back
and on leaving — moved to `shared/ui` as `SportPillFrame`, which takes the sports to offer, the sport
the page is on and its words, and reports a pick of another sport. **Every word is the caller's**:
_Shows this group for another sport you play_ and _+ Another sport_ are this page's, so
`SportFilterFrame` hands them in (`groupsCopy`'s `filter`), with `useGroupSport`'s state and the
offer behind _+ Another sport_. Nothing changed on screen: the group page's router suites are
unchanged, and the bar's own suite moved with it.

**Four tabs since #847, and the page always opens on Games** (story 59; ADR-0188 §5 keeps which tab
nowhere; Q125). Games, Fill in, You’re in and Friends are each drawn for the filter's sport; Info is the group's own
screen, opened from the header (below). **Every starting
tab has one dark card whose remedy is the link** (`LinkCard`): a headline, what the app is waiting
for, and **Share the link** (volt) beside **Copy link** (`onDark`). Share hands the phone's own
sheet one sentence — _Join my rakieta group on Rakieta: <link>_, the administrator's WhatsApp words
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

**The starting card counts members, not players of the sport** (stories 66–67; Fill in's card until
#847, You’re in's since). _No games yet — it's just you_ while the reader is the only member, _No
games yet_ once anybody has joined: a posted game is seen by everybody who arrives with the link.
**+ Post a game** is the primary button over the page's bottom corner, on You’re in (Fill in until
#847) — drawn disabled until posting shipped, and since #558 the door to _Post a game_ (below).

**Friends is the court a game with friends is built on** (stories 68–70; since
[#757](https://github.com/Rakieta02/Rakieta/issues/757), the friends screens §7.1–§7.2, friends 7–8).
**Competitive · For fun sets this game's kind, and nothing else's** (ADR-0202; the friends README's
defaults): it is `friendsGame.store`'s, no longer `gameIntent.store`'s, so turning it never moves the
Games deck's kind or the Play intent, and the deck's kind never moves it. It keeps its position while
the app is open, in memory only (ADR-0188 §5) — one value for the app, since it is the kind of the
game being built — and, like the app's other process stores, a sign-out does not reset it.

**The kind is picked in the Friends tab's menu, and the court sits right under the tabs**
([#861](https://github.com/Rakieta02/Rakieta/issues/861), PRD #859; the friends screens §7.1, tab menu
mocks 2 and 4 as illustrations). The _Competitive | For fun_ row above the court is gone, and the
court keeps its size. **Whenever the court is drawn** — not on the _add a sport_ card, not on the
level door — the selected Friends tab draws a chevron, widens for it, and is spoken _Friends,
Competitive_ with its expanded state; **a press on it opens the menu** (`shared/ui`'s `TabMenu`, 9.5),
hanging from the tab by its right edge: _Competitive_ then _For fun_, the current kind ticked, **no
counts and no door** — a game with friends is one game's kind, so a Competitive-only player picks For
fun here freely. **Picking the other kind** folds the menu away and turns the court into that kind's
game, and with every seat filled the card asks again for it, as it did; the kind it already is just
closes the menu. **The menu's open state is the page's own** (`GroupScreen`), drawn as the page's
last layer, never on the modal stage: a press on the tab again, a line, anywhere else on the page —
which does nothing else, the body taking no touch under it — Android back, a pushed screen, the
bottom bar and a sport change all close it, and another tab is one tap. **A pick asks the court**
through a handle (`FriendsTabHandle`), because a kind changed keeps the sides the court shows and
only the court knows what it shows. Walked in `friendsGame.test.tsx` through `test-support/tabMenu.ts`
(_open a tab's menu, then pick a kind_), with the chevron's absent states in `officialGroups.test.tsx`
and `theDoorWherePlayBegins.test.tsx`. **Not seen on a device** — the chevron, the widened tab and the
menu over the court are asked for a look (#866).

**The court is the app's court, spoken in the seat's sentences.** `Court` at `court.build` with
`shared/ui`'s `SeatFace` and `SeatCaption` — Play's until #574, and drawn by Fill in and a booked
game's players card too — and the reader in the first seat, captioned _You 2,71_. **A seated friend**
is their face, the seat's three letters over their Level, and 7.12's seat-clear badge — 6.9's remove
square, standing half over the face's corner as friends 7 draws each ×, so the face keeps its own
press (design-system Part 16, 2026-11-07). **An empty seat** is a dashed ring with a white plus that
opens the picker, as **+ Friends** does. Who sits on which side is the seat's rule (`seatPlaces`, a
side is a team, so squash's other seat is _their side_) and every seat says so in the seat's
sentences (`shared/vocabulary`'s, #574): _Padel, 4 of 4 seats filled._ first, then _Your side, you,
level 2,71_, _Your side, your partner, ewa.m, level 2,60_, _Their side, empty_; the × is _Remove
ania.k from their side_. **Side labels are drawn on padel and badminton only**, as the mocks draw
them: squash has no halves, and tennis's far seat stands where the label would be written.

**The line-up is `friendsLineUp`'s rules over the page's store.** The seats beside the reader in
court order — in doubles the partner first, then their side — and four acts on them: **Done** seats
the picks (those still picked keep their seats, the others fill the empty ones, a court picked for
the same friends stays), a **swap** trades two faces (tap one, its ring turns volt; tap another; tap
the first again to let it go — the reader never moves, standing first on their side as the card
reads it), the **×** empties a seat (and drops a court picked for the four), and a court picked in
_Find a court_. **The sides are the card's**: right after Done the card is read with no partner and
answers the evenest sides, and **the court draws what it answered**, so the court and the card always
name the same sides (the friends README, note 3). The moment the player acts on the court — a swap,
a ×, a kind or a court — what the court shows becomes the player's own arrangement (`pinned`) and the
card is asked with that partner, so a re-read never moves a face the player is looking at. The
friends are sent in the order the line-up holds them, which a read never changes, so the card is
not asked again because it answered.

**The line-up is one per group and sport, and goes with the page**, as _Post a game_'s draft goes:
a store rather than the tab's state because the picker, pushed over the page, seats its picks on
Done. The page opens on an empty court the next time. **`useFriendsGameOn` is where the rules meet
the reads** — the store, the picker's list, the card and the re-read a refusal asks for — so
`FriendsTab` only draws.

**A seat open: _Seat 1 more friend_** (_Seat 3 more friends_ on an empty court), **+ Friends**, and no
card (Q16). **Every seat filled: `proposals`' friends card** under the court, in the page's scroller
with it (friends 8), handed the line-up, the friends seated (their nicknames and Levels in the
sport, the picker's read) and two answers back — a row picked in _Find a court_, and a court picked
that is no longer for sale (`court_hour_not_for_sale`), which the page lets go so the card proposes
its own. The record of the card is [`proposals.md`](proposals.md#the-friends-card-and-find-a-court-757).

**The faces are the picker's read** (`friends`' `useFriendsIn`) — the same list, so a face is the
row it was picked from. **A friend who is no longer one leaves an empty seat** once that list is read
again (`withoutStrangers`, the mechanics §7.5), and a card refused `not_a_friend` or `no_level` reads
it again.

**The reader's face is the roster's, and their own record's only when it must be.** The group's
read carries the first rated in each sport, which is the reader in nearly every group; one who
joined after a court's worth gets their photograph from their own record (`player_record`'s
`useOwnFace`, a read asked only then), and the poster until it answers.

**The Friends screen is `friends`' page as a picker** (#757; the screens §4.2), pushed at
`/play/group/[groupId]/friends?sport=…` — the sport a validated route param, because the picker
lists Levels in it and the court it seats has its seats. This feature composes it: `FriendsPage`
with this feature's group tiles and Members as the Add friends sheet's doors, `FriendsPicker` as its
body, and **Done** (primary, `lg`) pinned at its foot. **The picks start as the court's seats** and
are the screen's own until Done; _back_ leaves the court as it was. A pick is held to the list, so
somebody seated who is no longer a friend is neither counted nor kept, and their seat is free to
fill. No tabs and no eyebrow — friends
3's header, as from You. **No friends yet** is this feature's empty card (play 55) — _Nobody you
know here yet_ and the link's doors — handed in as the picker's empty state. The page's route moved
to `[groupId]/index` to make room for it.

**Not seen on a device** (#757 asks for the walk): the × half over a face at the court's corners,
and whether Android delivers a press to the half of it outside the seat; the court and the card
scrolling together (friends 8); the swap's volt ring; the picker's greyed rows.

**Sent, the court is empty again** ([#759](https://github.com/Rakieta02/Rakieta/issues/759); the
friends screens §8): the card's _Send game and pay_ is `proposals`' (`SendGame`), and its `onSent`
is `useFriendsGameOn`'s `sent` — the line-up put back to an empty court, as the page opens on. The
kind stays where it stood. The game itself is on Home, in Your games.

**Three things the group page's mocks draw that this record departs from**
([#513](https://github.com/Rakieta02/Rakieta/issues/513), design-system Part 16). The Games card's
faces are **the face box, not circles** — this app has no round face (#338) — and **no face carries
initials**, which ADR-0167 §3 fences to the yes screen's tile; widening that fence is an amendment
to the ADR, not a drawing call. **+ Post a game** is **the primary button at 4.2's corner** rather
than the mocks' coral pill with a glow: the pill is the chip's and the yes screen's, the glow the
⚡Play disc's (disabled until #558 opened it). All three are flagged for the product owner. **Nothing on the page has
been seen on a device** — the unfold's pace, and whether four sports fit the bar on a 320pt phone,
are asked for a look.

**The header opens Info** (Q125, the product owner's ruling of 2026-11-02, [#721](https://github.com/Rakieta02/Rakieta/issues/721)).
Info was a fourth tab; the page now carries only the tabs drawn for a sport (three then, four since
#847), and Info — about
the group, not one of its sports — opens from the group's own header, as WhatsApp, Telegram and
iMessage open a group's info. **The tile, the name with the official mark and _N members · Home
club_ are one button** (`GroupHeader` over `ScreenHeader`'s `onPress`), spoken by the group's name
with the hint _Opens Info_: the whole header rather than the tile alone, because the tile is a small
target. **The back arrow and the sport pill keep their own taps** — the header's row is the button
and they are the deeper responders, which leaves the tile a direct child of the row, where the
filter's `cover` measures it. **While the filter's bar is open it covers the tile**, over a backdrop
across the page, so a tap there is the bar's. Info is **pushed over the page** at
`/play/group/[groupId]/info`, so the page stays mounted under it with its tab in `groupTab.store`:
**back from Info is the tab the player left** — the tab _Post a game_ was opened from after backing out of it, You’re in after a post (#848), the deck at a notice's
card. Members and Edit group are pushed over Info now, so back from each is Info. **Not seen on a
device**: the row's pressed look, and the badge on the 36pt tile and beside the open bar, are asked
for a look.

**Info is the group rather than a sport of it** ([#514](https://github.com/Rakieta02/Rakieta/issues/514),
stories 71–79; play 57–60, club 20), and its own screen since Q125 (`GroupInfoScreen`). **Its header is
the page's without the sport pill, and presses nothing**; its body is unchanged. Top to bottom: **the
link card** — the link in mono on one line, cut in the middle so its code stays in view, and
**Share** and **Copy** beside it, drawn short and spoken whole (_Share the link_, _Copy link_), the
same two doors as every other dark card on the page; **Want to join · N**, the Owner's; **the
members row**; and **Edit group**, the Owner's. **The way out stands at the screen's foot**, under
what scrolls rather than in it (#529 F1), so it is in the same place however long the queue above it
grows, and success lands on the Groups list past the page (`dismissTo`). Info never waits for the
filter's sport, because nothing on it is drawn for one.

**The Owner's count of waiting requests is on the tile's corner** ([#529](https://github.com/Rakieta02/Rakieta/issues/529)
D6; the Info tab's until Q125). It is the badge the tab carried — the Chats badge at the segment's
size, `CornerBadge` (lifted out of `Segment`, which draws it over Games, Fill in and You’re in), `size.segmentBadge`
— over the tile's top-right corner, on the page from every tab and on Info's header, and **spoken
with the header** (_Kazimierz crew, 8 members · Centrum Ruchu, 2 requests waiting_), so an Owner on
Games knows somebody is asking. It reads the Owner's requests under the same key as _Want to join_,
so the page asks for them as it opens, and an answer that takes a row on Info takes it off the tile
in the same frame — the page shows the new count on the way back. Nobody but the Owner reads the
requests, so nobody else's tile carries a count. A player group's header with no count is named by
its drawn words, not labelled with them (`groupHeaderLabel`).

**Info re-reads when it opens, on a pull, and on coming back to it** (#529 F2, Q125) — the group and
everything read under it that is on screen: who is waiting, the members row, the count. Opening it
re-reads what the page asked for as it opened, one more read of the group and the requests paid on a
tap, because what another phone changed meanwhile has to be on it without a pull; coming back from
Members or Edit group is `useOnReturn`. **The page no longer re-reads on a return**: only Info did,
and Info is its own screen now; what Info's writes change they write into the group's read, which the
page draws too. Games, Fill in and You’re in pull (below); Friends keeps none.

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
([#566](https://github.com/Rakieta02/Rakieta/issues/566)). **A refused list
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
([#516](https://github.com/Rakieta02/Rakieta/issues/516); [`administrator.md`](administrator.md)). An
official group is a Group, so the tile, the dots, the group forms' two cards, the request row, a
failed read, the row face, the stacked faces and the words they share are exported for that one
caller, and the dependency points one way. Four changes made the lending possible without changing
what this feature draws: **the members row's faces left `InfoTab`** (now `GroupInfoScreen`) for `FaceStack`, which the members
card on an official group's page draws too; **the request row left `WantToJoin`** for `RequestRow`,
which answers nothing itself — the two taps are props, so an Owner's queue and an Administrator's each
answer through their own routes, as #514's handover suggested; **_Who can join_ can be drawn without its _no sport to pick_ note**
(`noSportNote`), which is false of an official group; and **the Name card takes a placeholder and an
error**, for _Same name as the WhatsApp group_ and a refusal said on the field. The share sentence is
the administrator's WhatsApp post too, as #513 already wrote it for. **Edit group's _LET IN · N_ card left the
screen** for `AdmittedCard` ([#517](https://github.com/Rakieta02/Rakieta/issues/517)), which an official
group's settings draw after the same switch to Anyone. **Edit group's _Let anyone join?_ sheet left
the screen** for `OpenToAnyoneSheet` (#529, 2026-10-02), which an official group's settings open
before the same switch, so an Administrator is asked in an Owner's words.

**An official group is a Group the player meets as one, told apart by what it plays and who
answers** ([#519](https://github.com/Rakieta02/Rakieta/issues/519), PRD #500 stories 40, 56, 57;
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
— on all four tabs, and in place of Members' list, with no pill and no _+ Post a game_. **The header
still opens Info**, because the way out is not a sport's: a member who cannot play a group's sports
must still be able to leave it. Each of its buttons, one per sport the group plays, is the
Skill passport's _Add a sport_ for that sport (`useAddASport`), so the questionnaire is onboarding's
and the pass ends where every pass begun there does — on the passport, not back on the group. A
declared list this build can name none of — an older build after a sport is added — is carried as
none (`toGroup`), so the page reads the group as a player group's rather than drawing nothing.

**Calls made here, open for the product owner** (design-system Part 16 has the card's): the whole
name on the approver line; Info's _the administrator approves joins_; the card on every tab
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

**`find_a_game` became `classic_play`** ([#550](https://github.com/Rakieta02/Rakieta/issues/550)),
and then went with the old loop ([#576](https://github.com/Rakieta02/Rakieta/issues/576)). Nothing
here changed either time: Play opens on Groups, and no flag decides it any more.

**Games is the deck** ([#553](https://github.com/Rakieta02/Rakieta/issues/553), the screens A1–A2).
`GamesTab` hands `proposals`' `GamesDeck` the kind the Games tab's menu stands on (below; the
switch's until #862) — the game-intent store, which Friends' kind no longer shares since #757 (it is
the Friends tab's menu's since #861) — each line picked in that menu, and the starting card
to draw while the segment deals nothing. **The starting card is unchanged** (_Just you so far_, _3 of
4_, _Nothing picked right now_), and _Nothing picked right now_ gains a third door under the link's
two, _Post a game_ — the floating button's own `PostAGame` (You’re in's since #847), in `LinkCard`'s `foot`, open since #558. **The tab bar counts Games** — the cards somebody is already In on with you, off
the same deck read the tab draws (`useGamesBadge`), in the requests count's mark and spoken _Games, 4 with
somebody In_; Fill in counts its rescues, and You’re in its rows (below). **Games lays itself out**:
the deck fills the page between the tabs and its three buttons, so `GroupScreen` draws it outside
the page's scroller, and the deck scrolls itself in the states that are not a deck. Every suite that
opens a group's page stubs the deck (`test-support/groupDeck`'s quiet deck); the tab's own walk is
`groupGames.test.tsx`. The record of the deck itself is [`proposals.md`](proposals.md).

**The deck's kind is picked in the Games tab's menu, and the cap line sits right under the tabs**
([#862](https://github.com/Rakieta02/Rakieta/issues/862), PRD #859; the screens A1, A2.1; tab menu
mocks 1 and 3 as illustrations). The deck's _Competitive · N / For fun · N_ row is gone: the weekly
cap's line and the offline note stand directly under the tabs, and the deck takes the height. **The
chevron's rule is the switch's**: the selected Games tab draws one where there is a sport to play —
no _add a sport_ card, no level door — and a deck read of this group and sport has come back with its
kinds, **of either kind** (`proposals`' `useGamesMenu`, off `kindMenu`). So none while the first read
is on its way, after it failed, or while the first-time question is up; and it stays while a newly
picked kind is read, drawn off the other kind's read, which carries the same pair of counts. **It
costs no request**: both kinds' reads are watched, never fetched — the badge's read and the deck's are
the ones that go out. The tab is spoken _Games, Competitive_, and **a press opens the menu** hung by
the tab's left edge: _Competitive_ then _For fun_, the deck's kind ticked, each live kind ending in
today's count (`kindMenuLines`, `switchSides`' numbers), the kind the intent doesn't want a door —
dimmed, no number, no tick — whose line closes the menu and opens the deck's `KindDoor` over the deck.
**While an intent answer or its finding is out the tab is still**: the chevron stays drawn so the bar
doesn't jump, and a press opens nothing — read off the two mutations' own state
(`usePlayIntentOnItsWay`, `proposalKeys.finding`), never a store's copy. **A pick goes to the deck**
through a handle (`GamesDeckHandle`), because the panel and its write are the deck's: a door opens
its panel; a live kind is chosen in `gameIntent.store` and drawn at once from a cached read, under the
deck's spinner from an uncached one and over its `ReadFailed` from a failed one, the menu working
throughout — a door drawn off the other kind's read opens over them too; the kind it stands on
changes nothing but a panel left open, which it shuts. **A press on the tab while the panel is open opens
the menu over it, and a live kind picked there closes the panel** — the switch's own rule, which the
grilling had left open (the screens A2.1). **A notice moving the deck's kind closes a menu left open**
(the arrival's effect). To read its sport above the body, **the page holds the filter's state itself**
(`useGroupSport` handed to `SportFilterFrame`), as Members' Administrator view does. Walked in
`groupGames.test.tsx` (every chevron state, the lines, the three loads, a notice),
`groupGamesDoor.test.tsx` (the door from the menu, its three answers, the still tab) and
`groupBadges.test.tsx` (opening the menu sees nothing) through `test-support/tabMenu.ts`, with the
absent states in `officialGroups.test.tsx` and `theDoorWherePlayBegins.test.tsx`. **Not seen on a
device** — the Games chevron, its menu over the deck and the cap line under the tabs are asked for a
look (#866).

**Fill in is `proposals`' board** ([#557](https://github.com/Rakieta02/Rakieta/issues/557), the screens
A1, A3; mocks 11–14). Until #847 split it, `GroupScreen` drew one board as the tab — _Seats to fill_,
the rescues the reader is offered, then _You’re in_, their own yeses on this group's games still
filling, each under a heading — and handed it the starting card above for a tab with no row in
either, as `GamesTab` hands the deck its own. **The tab bar counts Fill in** — the rescues, the board
read's own `badge` until #849 (`useFillInBadge`, below), spoken _Fill in, 1 seat to fill_ — read for the page's sport
whichever tab is open, so `stubGroupDeck` now serves an empty Fill in too and every suite that opens a
page gets it. The tab's walk is `groupFillIn.test.tsx`; the board's record is
[`proposals.md`](proposals.md).

**You’re in is a tab of its own** ([#847](https://github.com/Rakieta02/Rakieta/issues/847), PRD #844;
the screens A1, A3; split mocks 1–3). **Four tabs, Games · Fill in · You’re in · Friends**, and the
two lists that shared Fill in get one each: `GROUP_TABS` gains `youreIn` after `fillIn`, so the tab
store, the route params and an onboarding pass's origin take it, and a tab this build does not know
is still dropped (`parseGroupRouteParams`). The label is _You’re in_, lower-case _i_ and the curly
apostrophe, like _Fill in_. **Fill in draws `FillInBoard`** — the rescues alone, no heading — and says
_No seats to fill right now_ with none, **never the starting card**, which tells you to post from a
tab that no longer has the button (split Q3b). **You’re in draws `YoureInBoard`** — the reader's live
yeses in this group and sport, no heading — and is handed the starting card (`YoureInTab`, which was
`FillInTab`): it draws it **only once both the rescue read and the live-yeses read have said there is
nothing**, never as a first frame, and otherwise _You haven’t said yes to a game here yet_. Each
tab's read is its own — its spinner, its offline note, its refusal with the retry — so one failing
never touches the other's rows. **+ Post a game floats over You’re in, and only there** (split
override 1: mock 1 draws it on Fill in), over the level door too, and not while an official group's
_add a sport_ card stands in the tab; You’re in's rows leave room for it, Fill in's no longer do.
**The tab bar counts You’re in** — a plain count of its rows until #849 (below), as Games and Fill in
counted, spoken _You’re in, 3 games_ (`useYoureInBadge`) — so **the live-yeses read starts as the page opens**,
from the tab bar, rather than when the tab is drawn: the read the tab makes anyway, made earlier, and
it holds up neither the page nor a tab switch. #847 had _Post a game_ turn the page to You’re in as it
opened, an interim #848 replaced (below). Walked in
`groupFillIn.test.tsx` and `groupYoureIn.test.tsx`. **Not seen on a device**: four tabs with badges on
a 320pt phone and at a large text size, which the split's log estimates at about 69pt a tab against
about 55pt for _You’re in_, are asked for a look.

**Fill in's and You’re in's badges count what the player hasn't seen**
([#849](https://github.com/Rakieta02/Rakieta/issues/849),
[ADR-0208](../../../docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md);
PRD #844; split Q2b, Q10–Q12). Until then a badge never cleared: _Fill in 2_ came back on every
visit until those games were gone. Now **a tab's rows are seen while it is on screen** — the page
in view, nothing pushed over it, no record sheet and nothing of the fill's up — **and the tab on
screen draws no badge**
(split override 2, overriding mocks 1 and 2): `TabsWithCounts` skips the selected tab. A visit
clears a badge, a row that only changed keeps its id and stays seen, and only a new one brings the
badge back; spoken _Fill in, 2 new seats to fill_ and _You’re in, 3 new games_ (`fillInTabLabel`,
`youreInTabLabel`). The rule, the ids, the marking and the phone's memory are `proposals`'
(`proposals.md`); what is this feature's is the tab bar and **whether the page is in view**, which
the route file reads (`useScreenInView`, the navigator's focus — read there and handed in, as the
hook's own rule asks) and `GroupScreen` hands each board as `inView`. **Remembered on the phone**,
per account, across a relaunch and Android killing the app, and forgotten at sign-out; the first run
shows today's counts until each tab is visited. **Games was untouched** — its plain count stood, on
the selected tab too — until #850 gave it the deck's ids (below). Walked in `groupBadges.test.tsx`.
**Not seen on a device**: a badge clearing on a visit and staying cleared after the app is killed
are asked for a look (the split's §17).

**The Games badge counts the cards with somebody In that the player hasn't seen, across both
kinds** ([#850](https://github.com/Rakieta02/Rakieta/issues/850), ADR-0208; PRD #844, split Q2b, Q10).
Until then it was the server's `games_badge`, which never cleared and was drawn on the selected tab
too. Now it is the deck read's ids (`in_card_ids`, #846, across both kinds) minus the ids seen, read
off the deck the tab already draws — **no extra request, and nothing reads the other kind's deck**;
`games_badge` stays on the wire and is not read. **Seen per kind**: while Games is on screen the deck
marks every card of the kind it is on, not only the top one, so the other kind's cards stay new
until the deck moves there — Marta, on Competitive, opens Games and leaves with _Games 1_ still there
for Kuba's For-fun yes, and it goes once she has switched to For fun (in the Games tab's menu since
#862, whose opening sees nothing). A notice that opens the deck at a card leaves its kind seen, like
any visit, because the deck moves there first. **The tab
on screen draws no badge**, now on Games too: `TabsWithCounts` skips the selected tab for all three
(split override 2), so the other kind's new cards show only once the player leaves Games — ADR-0208's
ruling. Spoken _Games, 4 new with somebody In_ (`gamesTabLabel`). This feature's part is the tab bar
and handing `inView` to `GamesTab`, which hands it to the deck — **false while a notice's kind is
still on its way to the deck** (`arrived`): the page moves the deck's kind in an effect that runs
after the deck's, and on a page whose reads are cached the deck would otherwise mark the kind it
stood on for one frame (the code review's catch). The marking is `proposals.md`'s.
Walked in `groupBadges.test.tsx` (the other kind's card, a visit on one kind, a kind picked, a changed
card, an older read of the other kind, a card this build cannot draw, a relaunch, sign-out, a
notice's card on a cold and a warm cache, and the details, a record and _It's a game!_ over the
deck). **Not seen on a device.**

**Games and Fill in re-read on a pull** (2026-10-12, asked by the product owner; You’re in too since
#847, the same control re-reading everything whichever tab is pulled). Until then only Info
pulled, and a game posted, a seat offered or a card filled on another phone reached the two tabs only
on a refocus or an answer's re-read. **One control and one spinner for the page** (`usePull`, the
Shell's drawing), re-reading on Games and Fill in the group — the header's count and the starting
cards' roster — and every read `proposals`
draws the two tabs from (`useRereadGroupGames`: the decks, Fill in, _You’re in_'s yeses and their
games), of which only those on screen go out at once. **Fill in's and You’re in's control is the page's scroller's**;
**Games' is handed to the deck**, which lays itself out and puts it on whichever scroller it is in —
the stage's among them (`proposals.md`). Friends keeps none — it was not asked for. Walked in
`groupGames.test.tsx`, `groupFillIn.test.tsx` and `groupYoureIn.test.tsx` (_pulling Games_, _pulling Fill in_, _pulling You’re in_). **Not seen on
a device** — the deck's pull shares the page with the card's drag, and only a thumb can say they keep
out of each other's way.

**_Post a game_ is `proposals`' screen over the page** ([#558](https://github.com/Rakieta02/Rakieta/issues/558),
the screens A5). Both doors — the floating button (Fill in's then, You’re in's since #847) and _Nothing picked right now_'s third — push
`/play/group/[groupId]/post`, whose route mounts `PostAGamePage`: it hands the screen the page's own
sport filter (`useGroupSport`), each sport's rated count off the group's roster, the page's sport and
the deck's kind; a reader rated in none of an official group's sports gets `AddSportCard` with _Get
rated in padel to post here_ (Q80). **Which tab the page is on is now a store** (`groupTab.store`)
rather than its state, because _Post a game_ reads it and moves it from over the page. Until #848 it
turned the page to Fill in **as it opened** (You’re in from #847), so every way back landed on the
yeses. The page forgets its entry — and the post's draft (`forgetPostDraft`) — when it goes, so it
still always opens on Games (story 51, ADR-0188 §5). The record of the screen is
[`proposals.md`](proposals.md); its walk `proposals/components/postAGame.test.tsx`.

**_Post a game_ backs out to the tab it came from, and a post lands on You’re in**
([#848](https://github.com/Rakieta02/Rakieta/issues/848), PRD #844; the screens A5). **Opening it no
longer turns the page.** `PostAGamePage` reads the page's tab once, as it opens — the store's entry,
or Games while the page has not moved off its opening tab — and that is the **origin**: the chevron,
the hardware back and the swipe all uncover the page as it was, on that tab, and back from Info after
it is that tab too. **The chevron names it**, _Back to You’re in_ or _Back to Games_
(`postAGameBackLabel`, the tab's own word, so the two cannot disagree); it replaced _Back to You’re
in_ for every door. The screen draws the chevron and nothing else, so the name is what a listener
hears — no mock draws the control, and the header's look is unchanged. **A post lands on You’re in**,
from either door, with the new game on the tab and _Posted — N of your best fits have it._ over it;
**so does a join from a cell's sheet** — a post's yes is on the tab, and a rescue's _It's a game!_
rises over the page with the page left on You’re in under it. Landing is the only thing that moves
the page: the store is set to You’re in, unseen, a moment before the screen goes. With no page under
it (opened by a link), a back-out opens the page on Games and a landing on You’re in. **Calls made
here**: a post that settles after the player has already backed out toasts and leaves the page on
the tab they backed out to — neither popping the page nor turning it under them; and an origin of
Fill in or Friends, which no door opens from today, is named and returned to like any tab. **A pass
begun from its level door or _add a sport_ card returns to You’re in**, whichever tab it was opened
from — where the button lives and a post lands. Walked in `postAGame.test.tsx` (both doors, each way
back, each landing) and the onboarding suites (the pass's return, opened over Games).

**A group's page opens at a card when a notice says so** ([#559](https://github.com/Rakieta02/Rakieta/issues/559);
the screens A9: _the deck opens with the card on top_). The route reads an **arrival** beside the
group's id — the card's sport, kind and id, all three or none (`parseGroupRouteParams`), spelled by
`groupDeckRoute`, which `notifications` pushes. The page stands on the card's sport until the player
picks another (`useGroupSport`'s `opening`, `openingSport`'s `wanted`) — **opening is not picking**, so
the phone's last sport is untouched — turns to Games, moves the deck to the card's kind
(`gameIntent.store`, one value for the app), shutting a Games menu left open (#862), and hands the
card to the deck as `onTop`. An arrival
this build cannot read opens the page as it always opens: the group's id alone is a page.

**Members' score tag is the served band, on every row** ([#660](https://github.com/Rakieta02/Rakieta/issues/660),
ADR-0195 §1). Every Members row carries `player_score` and `reliability_band` since the backend's
#659 — everyone starts at 100 — so `GroupMember.playerScore` is no longer optional and the tag is
drawn on every row; _no record, no tag_ is gone with the absence it drew. The tint is **the band
the server served**, never the figure's: VERY_HIGH mint, HIGH neutral, MEDIUM amber, LOW red, and a
band this build cannot name on the neutral tint — `player_record`'s `toReliabilityBand` narrows the
code in `toGroupMembers`, so the list and the record it opens read one band one way, and the phone
holds no 90 / 70 / 50 of its own (the 2026-10-01 paragraph's `scoreBand`, with its _70 is the
matcher's `SCORE_MIN`_, is retired). **The row says the band in words**: _Karol Tomczak, reliability
75, High, admin, Padel 2,75_ — the copy's `score` became `reliability`, and the band's word is
`player_record`'s `RELIABILITY_BAND_WORD`, because the tint is now a served fact and colour is never
its only carrier. Members carries no _New_, so a new player's tag reads `100` in mint. Tapping a row
opens the same sheet the player reads about themselves: the figure with the band's word or _New_,
and the four counts under _Full record_ (`player_record.md`).

**Members, requests and _… runs this group_ name the nickname** ([#728](https://github.com/Rakieta02/Rakieta/issues/728), [ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1, §4). The
members, the people, the join requests and the Owner's _approves joins_ line read the wire's
`nickname` / `owner_nickname` into the same fields, whole and never with an @. **An official
group's runner is the one value that is not always a nickname**: `administrator_nickname` is the
Administrator's nickname once they have one and the name their club typed until then (§4), so an
Administrator who has never played is still named, and `administratorName` keeps its word for that
reason. `groupInfo.test.tsx` holds _ania.k_ on a Members row.

**An official group's card begins a pass that comes back to the page**
([#729](https://github.com/Rakieta02/Rakieta/issues/729), ADR-0200 §3, §5), which rules the
_pass ending on the passport_ call above: its buttons say _Rate Padel_, `AddSportCard` takes the
group and the tab to come back to, and the page reads the tab and the sport off the route as
`returning`. The whole of it is in [`onboarding.md`](onboarding.md), whose pass it is.

**A player group's reader rated in nothing meets the level door**
([#730](https://github.com/Rakieta02/Rakieta/issues/730), ADR-0200 §2, §4, §6). `needsALevel(rated,
declared)` — a player group, rated in no sport — rides on `useGroupSport` and is handed to
`SportFilterPage`'s children as a third argument; where it holds, Games, Fill in, You’re in (#847) and Friends draw
onboarding's `LevelDoor` in place of their content, Members draws it in place of the list she is
on nobody's copy of, and _Post a game_ draws it in place of _Get rated in … to post here_, each
returning to the tab #729's card returns to. **_+ Post a game_ still floats over the door** — Fill in's until #847, You’re in's since —
(the screens A3), and opens _Post a game_'s. **The sport pill is drawn only once there is a rating to list**,
and lists only rated sports — which `filterSports` already made true; the door makes it visible.
An official group keeps `AddSportCard`. The words and the reads are onboarding's
([`onboarding.md`](onboarding.md)).

**The chip ends with _+ Another sport_, and Home asks a member rated in nothing**
([#731](https://github.com/Rakieta02/Rakieta/issues/731), ADR-0200 §4, §7). `sportsToOffer(rated,
declared)` is what it offers — every sport the reader is unrated in, in a player group; an official
group's own sports she is missing, in one — and **nothing while there is no chip** (the door or the
group's card asks then) or once nothing is left. It rides on `useGroupSport` as `toOffer`.
`SportFilterPage` takes `onAnother(offer)`: while the offer is not empty, **the pill unfolds even for
one rated sport** — a choice of one is a choice again, so _A player rated in one sport gets a plain
label_ above now holds only where nothing is left to offer, which in a player group means rated in
all four — and the bar ends with **_+ Another sport_**, drawn with its plus and spoken without, the
farthest pill from the current sport and so the last to slide out. Pressed, the bar folds and the
page replaces to onboarding's picker over the offer (`anotherSportRoute`), for a pass that returns
to its tab: the page's own, and on Members the page's beneath it, as #729's card does. The
Administrator's Members hands none. **Home's card is `HomeLevelCard`**, which the shell draws:
onboarding's `LevelDoor` `from` Home, where `homeAsksForALevel(groups, rated)` — a member of at
least one group, player or official, holding no rating. **`useHomeAsksForALevel` reads the ratings
first and the groups only for a player rated in nothing** (`useMyGroups({ enabled })`) — though Home
reads the groups for everybody since #800, for _Your games_' groupless line — so the card costs one read — `GET /ratings` on every visit, the price of the card, which every group's chip
shares — and it draws nothing until both have answered and nothing on a failure: it is a nudge,
never a wall. **A friend's ask for a level stands in its place** ([#765](https://github.com/Rakieta02/Rakieta/issues/765),
Q129): the rule is `homeAsksForALevel(groups, rated, askedForALevel)` now, over `proposals`'
`useHomeLevelAsks` too — nothing while Home's ASKED FOR A LEVEL holds a card or Home has yet to
answer, and the card again once the row is empty; a Home read refused or offline holds none. `groupKeys` is exported for the notice that opens Home on it, which marks the groups
list stale with the ratings. **#816 dropped that hand-off** (ADR-0205 §4, Q13): a friend's ask waits
in Needs your answer, behind the header's envelope, and is never drawn in the card's place, so the
rule is `homeAsksForALevel(groups, rated)` again and the hook reads no Home. The card shows above
_Your games_ whenever she is in a group and rated in nothing, whether or not someone asked. The walk is
`friends`' `levelAsks.test.tsx` (_Get your level on Home_).
**Calls made here**: _+ Another sport_ is the bar's farthest pill rather than a chip of its own
beside the pill (no mock draws it); Members' chip carries it too; the pill's hint for an unfold onto
it alone is _Offers another sport to rate_. **Not seen on a device**: the pill and the bar with
_+ Another sport_ in them, and their unfold.

**Members' rows end in the reader's relation to them** ([#753](https://github.com/Rakieta02/Rakieta/issues/753),
[ADR-0202](../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§1; the friends screens §1). Every row but yours is handed, as it was, to `friends`' `RowWithFriendEnd`,
which puts **+ Add**, _request sent_, _friend_ or **Accept** on its right — **the rows keep today's
design** (the friends README's override 1), and the PRD #500 refusal of a friend tag that stood in
`MembersScreen` is gone with it. The pill is a sibling of the row's press, so a tap on the rest of the
row still opens the record and only the pill asks. A request asked here names this group and the
pill's sport, which the other person's Home card says; the list's own re-read is handed in, so the
row turns on the server's answer. **A record opened from a row and closed re-reads the list**: what
was pressed on it — Add friend, Accept, Remove, Block — moves the row it was opened from, and the
record reads `friends`' acts, not this list's key. The record is handed the group (`groupId`), for a
request asked there. **The Administrator's Members draws no ends** (`MembersList`'s `friends`, off in
the administrator area). The record of why the end looks as it does is [`friends.md`](friends.md).

**A group's tile, by id, for the Add friends sheet** ([#754](https://github.com/Rakieta02/Rakieta/issues/754)).
`MyGroupMonogram` draws one of the reader's groups' tiles off their own Groups list (`useMyGroups`),
its box held empty until the list is in: the sheet's read names no tile, and a group's letters are
cut once, by the server (ADR-0183 §5). The shell hands it, and `groupMembersRoute`, to `friends`' page.

**The Friends screen hands the picker its group, and a notice opens it with the page under it**
([#758](https://github.com/Rakieta02/Rakieta/issues/758)). `FriendsPicker` takes `groupId`, the group an
ask for a Level is made from, whose picker the friend's answer opens for the asker
([`friends.md`](friends.md)). **`groupPickerRoutes(groupId, sport)`** is where _Level got_ lands: the
page on its Friends tab standing on the sport — `groupReturnRoute`'s params, the way a returning pass
stands on one, so opening is not picking — and the Friends screen over it, so Done seats the picks
on that court and _back_ is the court, as from _+ Friends_; `notifications` pushes the two
([`notifications.md`](notifications.md)).

**Home's HOTTEST GROUPS is this feature's row** ([#800](https://github.com/Rakieta02/Rakieta/issues/800),
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§3; the Home rows screens §3, the mechanics §5; home rows 3–6, 21). `HottestGroupsRow` reads
`GET /hottest-groups` (`useHottestGroups`, keyed `groupKeys.hottest()`) and draws up to six cards on
the shared row frame (`HomeRow`, `HomeRowRail`, #798), peeking, in the read's order, with no See all;
**nothing while the read is empty, in flight or failed** — the screens §1's call, the rest of Home
standing. The shell draws it just below _Your games_ and re-reads it on Home's pull
(`rereadHomeGroups`, with the Groups list); **a return to Home re-reads it once its read is older than thirty seconds**
(`refetchQueries` with `stale: true` on `useOnReturn`), the app's `staleTime`, and foregrounding does
the same through the focus manager. **Every figure is the server's** — the heat share, the tag, the
order, the faces, the friends count, `run_by` — so the phone's half (`domain/hottest.ts`) is what a
card offers (`hottestChip`, which is `groupAction`: an Administrator who runs an official group reads
_Join_ whatever its policy), the sheet's one button (`sheetButton`: _Open group_ for a member), four
faces on the card and six on the sheet, and a bar held inside its track. **The card is two doors**:
the chip acts, anywhere else opens the group sheet (`HottestGroupCard`; design-system 7.30). **The
group sheet and the withdraw sheet are one `BottomSheet`** whose title, title-row button
(`BottomSheet`'s new `action`) and body swap — _Asked_ on the group sheet turns it into _Waiting for
Ogrody 33 to answer_ · **Withdraw request** — because iOS drops a second native window opened while the
first closes; nothing on it but its button presses (Q26), and _Open group_ is the row's callback, so no
navigation hook sits inside the sheet. **The chip moves at once** (the screens §3.4): `useJoinGroup`
now guesses a Hottest card's relation from its own policy on the tap and lands the answer's relation
over the guess, putting the one card back with a toast on a refusal; `useWithdrawJoinRequest` does the
same for `DELETE …/join-request`, which refuses nothing. A tap on a card whose write is in flight is
let go — any card's, found by the writes' shared mutation key (`useRelationWritesInFlight`). **After either, the row, the Groups list and Home's own read are read again**; the searches
are written, never re-read — a search read again landed its older relation over the join's answer.
Leaving a group re-reads the row too. **_Your games_' groupless line** is the shell's to place and
this feature's to answer: `useInNoGroup` is `true` only once the Groups list has answered with none,
and the words are `GROUPS_COPY.hottest.groupless`. So **Home reads `GET /groups` for every reader
now**, where `HomeLevelCard` read it only for a player rated in nothing — the price of the line; the
card's own rule is unchanged. The words are §31.1–§31.4's in `groupsCopy.ts` and
`groupsPresentation.ts`. **Calls made here**: _Waiting for an answer_ for an Owner who can no longer
be named; the identity line leaves the runner out for one; _1 game this week_ in the singular (§31.2's
call); the chip's spoken names (_Ogrody 33 Club: Asked_) and the withdraw sheet's spoken close,
_Keep the request_, neither in §31; _Withdraw request_ is the outlined
`secondary` button, since the system has no destructive-outline one. **Not seen on a device**: the
card, the band's stripes, the shield, the heat bar, both sheets — against home rows 3–6 and 21.

**HOTTEST GROUPS is FOR YOU's first line, _Groups heating up_** ([#820](https://github.com/Rakieta02/Rakieta/issues/820);
ADR-0205 §5; home refactor 5). `HottestGroupsRow` became `useHottestGroupsLine`, which hands the shell
the line's title (`GROUPS_COPY.hottest.line`), its cards on the peeking rail — now settling on their
edges — and the group sheet, or `undefined` while the read is empty, out or failed. **No footer**
until the Groups heating up page has one to open (#823). The cards, the chips, both sheets and every
write are unchanged (the slimmer card is #821's). **A reader in no group** finds the line open from
the start — the shell's call, from `useInNoGroup` — and reads _Join a group to get games — see Groups
heating up, just below._ (`hottest.groupless`). Walked in `hottestGroups.test.tsx`: the line first
under FOR YOU, closed; open onto the cards with no footer; hidden empty or failed; closed and gone
when it empties while open, back closed; and the groupless line with the line open, kept open by a
join from it.

**The slimmer card** ([#821](https://github.com/Rakieta02/Rakieta/issues/821); ADR-0205 §5, Q22; home
refactor 5.1). Open in Groups heating up, a card is the striped band, the tag, the shield, the name,
**_N games this week_ on the left and _N players_ on the right** (`Figure`'s `end`, held against the
card's edge), the faces and the chip. **Gone: the heat bar, _+N this month_ and the sport line**, dots
and names — and with them `heatFill`, `size.hottest.heatBar` and the copy's `thisMonth`. The heat still
orders the groups and picks the tags on the server, and the read still serves `heatShare`; nothing
draws it. **The card is spoken as drawn**: `hottestCardLabel` no longer says _3 new this month_.
**The group sheet is unchanged** and keeps the sports with their dots and _players · new this month_
with the green _+3_ — `Growth` moved into `HottestGroupSheet`, its only user now. The card is shorter by
the sport line and the bar; its spacing is otherwise today's, a look to make on the device rather than
a number read off 5.1. Walked in `hottestGroups.test.tsx`: the two figures, left and right, the spoken
name, nothing removed drawn on any card, and the sheet's every detail. **Not seen on a device** — a look
is owed against home refactor 5.1: the figures' places, the card's height without the bar, the faces
and chip at its foot.

**Groups heating up counts the groups to look through** ([#822](https://github.com/Rakieta02/Rakieta/issues/822);
ADR-0205 §6; the mechanics §5.10; home refactor 3, 4). The read keeps the server's **`total`** beside
its six cards — `HottestRow` (`toHottestRow`), every group of 3 or more players, the reader's own
included, counted up to 100 — and the line hands it to the shell as its `count`, drawn _99+_ past 99.
**`withRelation` now moves a card on the row and leaves the total**: a join, an ask or a withdraw draws
the card at once, and the re-read every such write asks for brings the server's new figure — never a
guess. **A refused join, ask or withdraw now reads the row again** when it had moved a card: the
guess cancels any read in flight — a pull's, a return's — and without a new read the row's cards and
its count would stand as they were before it. No footer still, so no _See all N_ here. Walked in
`hottestGroups.test.tsx` (the count moving with a join's re-read, and not before it lands; a refusal
reading the row again), `hottest.test.ts` and the mapper test.

**The Groups heating up page** ([#823](https://github.com/Rakieta02/Rakieta/issues/823); ADR-0205 §7;
the Home rows screens §3.6, the mechanics §5.10; the words §31.14). **The line's footer reads _All
groups ›_** (`FoldingLineFooter`, spoken _All groups heating up_), which pushes `HottestGroupsScreen`
over Home at **`/hottest-groups`** (`HOTTEST_GROUPS_ROUTE`) — the one groups screen not under Play, so
the shell lists it in `PUSHED_SCREENS` and inside Home's tab, as it does the people See all screens.
**It reads `GET /hottest-groups/all?after`** (`useHottestGroupsPage`, an infinite query keyed
`groupKeys.hottestAll()`, `LISTS_PEOPLE` like the row, since its faces are friends first): every group
of 3 or more, the reader's own included, in the row's order, 20 to a page by the server's cursor
(`HottestPage`, `toHottestPage`), the next read as the list nears its end. **A group a later page reads
again is drawn once** (`joinHottestPages`): heat is worked out on every read, so one that cooled
behind a cursor comes back. **The row and the page are two keys under one root** —
`groupKeys.hottest()` is now `['groups', 'hottest', 'row']`, `hottestAll()` its sibling, and
`hottestReads()` both — so a relation write cancels and re-reads the two at once, while a return to
Home still re-reads the row alone and never a page left behind. **An end is owed until a page behind it
draws something new**: the list says it reached its end only when it has grown since, so
`useHottestGroupsPage` remembers an end it was asked for and asks again once the reads settle, when the
page never landed — a write cancels the page on its way, and its re-read reads only the pages drawn —
when a re-read was in flight, or when the page brought back only groups the list already holds
(rankings' `owedEnd`, widened). **The frame is the people See all screens'** — the header, the states,
the pull, the later page's failure under the list — written again here without the sport pill, since
the page has no filter and `SeeAllScreen` and `useSeeAllPages` are `discovery`'s, keyed by player.
With rankings' General that makes three paged lists of the same shape: a shared frame and paging hook
are owed, to a ticket of their own, and `discovery`'s does not yet ask again for an owed end. **The
cards are the line's `HottestGroupCard`** at the content's whole width, and **the taps are the line's**:
the group sheet, the withdraw sheet and the chips moved out of `HottestGroupsLine` into
`useHottestTaps`, which both draw. **A read that drops the sheet's card closes the sheet for good**, so
a later read bringing it back opens nothing (`usePersonSheet`'s rule; until now the line's sheet came
back by itself). **One write, both reads** (`useGroupWrites`): a join, an ask or a withdraw guesses the
card's relation on Home's row and on every page read, wherever it was tapped — **each copy by its own
policy**, since the two are separate reads — both reads cancelled first, as the row's was; it lands the
answer on both, and reads both again with the Groups list and Home; a refusal puts each back where it
stood. Leaving a group re-reads the page too. **Left as they were**: a write re-reads every page drawn,
one after another, as See all's friend writes do; and an edit or an approval re-reads neither the row
nor the page, as before.
**Calls made here**: the link's spoken name; _No groups heating up right now_ for a list read empty, met
only when every group fell under 3 since the line was read; the page draws no count. Walked in
`hottestGroupsPage.test.tsx`: the footer opening the page, the Home tab lit and no pill; the served
order with the line's six first; _You're in_ on the reader's own groups, past the six too; the card at
the content's width; 20 to a page, never twice, nothing past the last; a next page a write cancelled,
and one that brought nothing new, each read on; reading, a first and a later page refused, an empty
list; the sheet from a card, and closed for good when a read drops it; _Join_ and _Ask to join_ on the
page drawn at once on Home's line; a page-only card's join; a refusal; _Asked_; _You're in_; and back
to Home with the line still open. **Not seen on a device** — a look is owed: the page's header, the full-width card, the
gaps and the pull.

**Games stays mounted while another tab is on, and the page reads its tabs ahead of the group**
(2026-11-24, a performance diagnosis on the A32). **Back to Games from any tab took ~0,4 s in a release
build and ~0,6 s in a debug one before anything moved**: the tab was unmounted on the way out, so the
way back drew the deck's three cards from nothing, and its remount read the deck again and drew them a
second time. The deck now stays mounted out of sight (`display: none`), sees nothing while it is
(`inView` is the page's and the tab's), and **reads again on its return if its read has gone stale** —
what the remount's own read used to bring (`GamesDeck`'s `onScreen`). The way back is ~0,1 s. **A first
open waited on a round trip it did not need**: the tabs are drawn once the group has been read, so the
deck, Fill in and the live yeses set out only then; while the group is on its way the page now asks for
them, and for the saved payment method a yes on the deck asks about, beside it
(`useReadGroupGamesAhead`, Query's prefetch — nothing still fresh is asked again). A first open's deck
landed ~1,4 s sooner. Walked in the router suites; `groupGames.test.tsx`'s failed reads now refuse
until the retry or the pull, since the read ahead meets the refusal first.

**Groups heating up shimmers while its first page is read** (2026-11-24,
[#872](https://github.com/Rakieta02/Rakieta/issues/872); PRD #867, the loading shimmer log §10; design
system 5.6). The spinner is gone. Under the real header, **the line's card stands as its skeleton at
the content's whole width, `sm` apart, as many as fill the screen** (`HottestGroupsScreen`'s
`HottestGroupsSkeleton`), on one `SkeletonGround`; the first page comes in on `Reveal`'s cross-fade once
its read finishes. See all's rules hold (`discovery.md`): the failure and the offline note take the
skeleton's place; the skeleton stays through Query's retries and stands again on _Try again_ or the
connection back; an empty first page says its line; a pull and a later page never show it. **The card
is 5.1's white card drawn as itself** (`HottestGroupCardSkeleton`), at the height its drawing gives it
(`hottestCardHeight`, its words' lines grown with the phone's text size), with the shapes every card
has: the band edge to edge, the shield over it in the card's white ring, the name, and both figures
over their words, set at the widths of _14 games this week_ and _11 players_. **Calls made here**: the tag (only the hottest few have one), the faces (as many
as the server sends) and the chip (its words are the reader's relation) are not drawn, and the foot
keeps their room; the spinner's spoken name went with the spinner. Walked in
`hottestGroupsPage.test.tsx`: the skeleton at the card's size filling the window, then the list; the
empty line; the retries, the failure and _Try again_; the offline note and the connection back; and a
pull. **Not seen on a device**: a look is owed at the card's shimmer and the fade onto the list.

**A group's page shimmers until it is built, then reveals together** (2026-11-25,
[#875](https://github.com/Rakieta02/Rakieta/issues/875); PRD #867, the loading shimmer log §10; design
system 5.6). It opened blank — a back arrow over nothing while the group was read, and nothing at all
offline. **Two parts, top-down** (`groupPageParts`): **the header and the tab bar**, which wait for
the group's read and the sport, and **the body of the tab on screen**, which waits for that tab's
first read (`proposals`' `useGroupTabRead`: the deck the tab draws, Fill in's rescues, or You’re
in's yeses — and with none here Fill in's too, since the starting card waits for it). While they
wait, on one `SkeletonGround`: **a monogram circle and a name bar** beside the real, pressable way
back (`GroupHeader`'s `shimmering`, no pill), **the tab bar's shape** under them
(`GroupPageSkeleton`), and the tab's own skeleton — **one deck-card block filling the stage** on
Games, **rows** on Fill in and You’re in (`DeckSkeleton`, `BoardSkeleton`). They come in on one
cross-fade once both parts have finished; **from 2.5 s after the page mounts the header and the tabs
come first and the body keeps its skeleton** (`useRevealParts`). **Switching to a tab with nothing
read shimmers only its body**: the scroller's `Reveal` is keyed by the tab, and a part once shown
stays shown. **The offline gaps are closed by the shared rule**: the group's read held for a
connection draws the amber note in the body, under the header's way back, and the deck's first read
held offline draws it where a spinner turned for ever (`proposals.md`). A part revealed with a
failure or the note shimmers again when its read sets out once more. **Unchanged**: _Finding …
games for you…_, the Friends card's _Building_, the kind door, the first-time question and the tab
menu. The kind swap's spinner became the same deck-card block in the stack's place (#876,
`proposals.md`).

**Calls made here**: **the group's read retrying after one failure keeps the page shimmering**
(`groupReadStage`) — the shared rule counts such a read finished so it cannot hold the rest of a
screen, but every part here draws from this one, so revealing it would show a back arrow over
nothing; a refusal or a hold is what ends it. **So does the ratings read** the sport is answered
from (`useGroupSport`'s `answered`): retrying, it keeps the page shimmering rather than revealing a
header with no pill over an empty body. **Friends waits on no read** — its court draws its own
_Building_ — and nor do the add-a-sport card and the level door, so they come in with the header.
**_+ Post a game_ comes in with the header and the tab bar**, never over a page still shimmering.
**What lies over the deck reveals Games**: from the ceiling the tab bar is in and its menu works, so a
door picked while the deck's first read is out opens its panel — and finding after it — over the
deck's own block, the tab revealed for it (`gamesRead`, the deck's `onCovered`), never under the
tab's skeleton, unseen.
**The header is not cross-faded**: its tile, name and pill take the skeleton's place as the tab bar
and the body fade in, as Home's numbers come with their part, because the way back must stay the
real one, pressable and spoken, throughout. **Each `Reveal` keeps its place in the tree from the first
frame** — Games', which is the body on Games until the group is read and the filter has said, and
the scroller's, keyed by the tab — so the fade carries the skeleton standing then into what replaces
it; an official group's add-a-sport card, which replaces Games' place, comes in without the fade.
Out of sight behind another tab, Games draws no skeleton. The skeletons stand at the phone's text
size; the tab bar's grows with `fontScale` from the segment's 25. Walked in `groupGames.test.tsx`
(the shapes and the way back; together, though the deck lands first; the header and the tabs from
the ceiling; the deck's block kept while the sport is read after the group, and through the ratings'
retry; both offline notes and the connection back), `groupGamesDoor.test.tsx` (a door opened over
the deck's block at the ceiling), `groupFillIn.test.tsx`
(a switch shimmering only the rows), the boards' suites, `joinGroup.test.tsx` (a group joined a
moment ago, opened from the list) and `groupPage.test.ts` (the parts' rule). **Not seen on a
device** — a look is owed (the phone walk, #877): the shapes' sizes against the page, the fade, and
the header's tile and name taking the circle's and the bar's place.

**Groups heating up's card stands a little bigger on Home** (2026-11-26; design-system 7.7, 7.30,
Part 16). On the line it is `lineCardRatio` (0,83) of the line's content, where it was 0,74 — 290 of
349 on a 411pt phone, the next card's edge 65 where it was 97 — as Players at your level's and Players
with your vibe's are (`discovery.md`). **It keeps its shape**: its height is its drawing's, so every
vertical gap grows by the width's factor (×1,6) onto the 3pt grid — 9·6·3·9·12 to 15·9·6·15·18 from the
shield to the foot (188 → 212), within half a grid step of growing as much as the width did. The band,
the shield, the words, the faces, the chip and the sides' inset are their own size. **The page keeps
its own** (`layout`: `'row'` on the line, `'page'` on the Groups heating up page), and so does its
skeleton (`hottestCardHeight`, the page's by default). Walked in `hottestGroups.test.tsx` (the line's
gaps, the height grown by the width's factor) and `hottestGroupsPage.test.tsx` (the page's gaps).
**Not seen on a device** — a look is owed on the A32.
