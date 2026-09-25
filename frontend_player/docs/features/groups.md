# groups — Play › Groups, New group, Join a group, and a group's page

> The design record for `src/features/groups/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**Play opens on Groups, and the feature is four screens over six routes**
([#512](https://github.com/Raketa02/Raketa/issues/512), PRD
[#500](https://github.com/Raketa02/Raketa/issues/500), ADR-0182, ADR-0183). With `find_a_game`
off — the code default since #512 — the Play tab draws the shell's _Groups | Explore_ segment
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
under one thumb.

**New group is the screen's own state and dies with it** (stories 11–27). Every open is empty and
the back arrow discards it. The name field stops at 40 characters (`GROUP_NAME_MAX`); the server
trims and counts again. The home club card (`HomeClubCard`) holds no state and draws five:
**empty** (the hint, and what a home club is for), **searching** (rows of name · district · sports
and _Set as home ›_, the whole row the tap, **no distance** — #512 overrides play 7), **no match**
(_No club called "…"_ and that only clubs in Raketa can be one), **a club with groups** (tinted
`amberSoft` to the card's edges, tagged _group already here_, a white strip per group with its
action — the player can join from inside the form, and can still choose the club, because a second
group at one club is allowed), and **chosen** (the field replaced by the club on `mintSoft` with
its distance and **Change**, and the line under it now saying what the choice means). _Who can
join_ is two chips, _Anyone_ first and chosen, with the note that there is no sport to pick.
**Create the group** is disabled until the schema answers a group, busy while the create is in flight — two
creates are two groups, and the create is never retried — and on success it seeds the page's read
with the answer, replaces the form with the page and raises _Group created_ in `ok`. A refusal the
form can name (`group_name_invalid`, `home_club_unknown`) is said under the button in the form's
words.

**Join a group is one field and nothing else** (stories 29–44). The field takes the focus as the
screen opens; **Paste** — a chip inside the field, through the new clipboard port — drops a link
from WhatsApp into it, and becomes **✕** while there is text, which clears the text and the
answer. A club's card header is **context, not a choice**: one spoken element with no button role,
name over _district · distance · sports_. Each group row draws its dots, count and approver on one
truncated line with the action beside it; the approver is the Owner's **whole Name** (ADR-0171 §4,
#505 — the row truncates it, nobody cuts a first name from it), _anyone can join_ for an Anyone
group, and _the owner approves joins_ for an Owner who can no longer be named. The three ways of
there being nothing are three sentences: _No groups here yet_ on a club's card, _Nothing at that
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
tell the four hues apart still gets them only from the group's page. And the home-club field's
focus ring is **coral**, as the ticket asks (_live, coral focus ring_), which is a seventh coral
beside 1.2's closed list; both are recorded in design-system Part 16 for the product owner to rule
on. **Nothing here has been seen on a device.**

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

**Four tabs, no counts, and the page always opens on Games** (story 59; ADR-0188 §5 keeps which
tab nowhere). Games, Fill in and Friends are each drawn for the filter's sport; Info is
[#514](https://github.com/Raketa02/Raketa/issues/514)'s and draws nothing yet. **Every starting
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
seen by everybody who arrives with the link. **+ Post a game** is the primary button, disabled, over
the page's bottom corner — drawn, inert, and `disabled` to a listener.

**Friends is a court with nobody to put on it yet** (stories 68–70; PRD #500 overrides play 49–56:
no friends feature). **Competitive · For fun** is a process-scoped store (`gameIntent.store`) —
it keeps its position when the player leaves the page and comes back, and ADR-0188 §5 keeps it off
the phone; one value for the app, since it is the intent of the game being built. Like the app's
other process stores, a sign-out does not reset it.

**The court is play's court, spoken in play's sentences.** `Court` at `court.build` with play's
`SeatFace` and `SeatCaption` through `play/types` — the edge `plans` and `games` already cross —
and the reader in the first seat, captioned _You 2,71_; every other seat is a dashed ring with a
white plus that opens **Friends**, as **+ Friends** does. Who sits on which side is play's rule
(`seatPlaces`, a side is a team, so squash's other seat is _their side_) and every seat says so in
play's sentences: _Padel, 1 of 4 seats filled._ first, then _Your side, you, level 2,71_, _Your
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
to the ADR, not a drawing call. **+ Post a game** is the **disabled primary button at 4.2's corner**
rather than the mocks' full-strength coral pill with a glow: the pill is the chip's and the yes
screen's, the glow the ⚡Play disc's, and a full-strength button that ignored its press would say the
opposite of what it does. All three are flagged for the product owner. **Nothing on the page has
been seen on a device** — the unfold's pace, and whether four sports fit the bar on a 320pt phone,
are asked for a look.
