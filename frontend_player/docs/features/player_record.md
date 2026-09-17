# player_record — the record sheet

> The design record for `src/features/player_record/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**A face opens the person, and the pairing gets a row**
([#384](https://github.com/Raketa02/Raketa/issues/384),
[#373](https://github.com/Raketa02/Raketa/issues/373)). Tapping a photograph on the balance
forecast used to open the **Fit breakdown** — the arithmetic of a _pairing_ — which answers a
question nobody asked by tapping a picture of a person. `features/player_record/` is what it
opens instead: the poster with the Level printed on it and the sport beneath, the on-court mark,
the whole handle, `In your area · 4 km` and one pill per rated sport; then the skill card — the
Level, how sure the platform is, 7.5's band bar and its likely-range bracket — and under it
**7.13's three record blocks**, `Player Score · Last 5 · Counted`, which is the row the
competitive candidate card already draws about the same three facts. Each figure is drawn
**once**: the reliability pill left the header and the counted figure left the skill headline,
because the two are inches apart in one card and a reader would otherwise meet `21 counted`
twice in two registers. The first block is titled **Player reliability** rather than _Player
Score_ — the domain term is untouched and the matcher still prices it, but _Score_ beside a
Level, a band and a run of form is a fourth number a reader can take for a rating, and
_reliability_ is the one word that says what it is not. The run is **that sport's** and never padded. `StatBox` moved to
`shared/ui` for it, which is `RunOfForm`'s and `PhotoPanel`'s promotion a third time and for
the stronger reason: not that two files use it, but that the padding, the ground and the two
type steps are **one specified shape**. The row is a **sibling** of the skill card and not a
footer on it, and that is an absence rather than a layout — two of the three come off the
resolved sport and the Player Score comes off the whole person, so a block nested in a card
drawn only when a Level resolves would take a ghosted newcomer's one figure down with the
sport. Its figure is `ink`: the sheet's one ladder stays on the metered rows that account for
that number, where a bar lifting is the thing a held player came to watch. The Fit breakdown is
not deleted: it moves behind **`Player fit 78` under the sport pills** — the sheet's one action,
and one a reader had to scroll past four zones to find while it was a card at the foot. It is
named for what it opens rather than for the question it answers, so the ✦ leaves the control's
own name; the figure stays beside it, because that number is what a reader is deciding whether
to ask about. It is deliberately **not a button**: 6.1's `primary` is coral, the app's one
accent, and a filled coral control in the header competed with the photograph beside it and
promised a _submit_. It is text with a target — the name in `ink`, the figure in the same
tabular mono every other number on the sheet uses, no fill, border or radius, `hit.btn` for
reach and opacity for the pressed state. It
is **present only where a pairing is behind the entry point** — your own face carries no candidate row, so it offers
none, and neither will a record opened later from a chat. It is a feature of its own rather than
`play`'s because the second and third doors are other screens', and the sheet **reads no global
state**: the subject, the arrival sport, the distance, the reader's own area and the pairing all
arrive as props.

**Your own face is a control for the first time**, because nothing served your row and there was
nothing behind it to open. It reads `GET /players/me/record`, which is the **ungated** route —
a block is between two people and a hold does not reach this screen — and the sheet retitles to
_How others see you_ with the distance gone, because the reliability number has been deciding
who you are offered to since you signed up and a penalty nobody can look up is a penalty nobody
can fix. Whether it retitles is the server's `is_self` and never a comparison this client made;
which route to ask is the court's own knowledge of which seat is yours.

**The refusal is one line and nothing else, and there is no retry on it.** Never disclosed,
blocked in either direction, held and no such player answer one code with one body, byte for
byte — a response that named which would deliver a block to the one person a block is meant to
be invisible to — so re-asking returns the refusal, and only a failure to _reach_ the platform
gets a control. A **withheld** seat is the one face that is not a control at all: the court has
already said the row is withheld, and a button that provably opens a refusal is the pool's own
_a control that returns nothing is a control lying about being useful_. **The tags drawn are the
record's own live list and the claim is the pairing's** (`domain/tagRow`): the engine's
`matched[]` supplies the tint, a tag published since the search draws untinted, and _No tags in
common_ is kept as the engine's claim and never invented — a candidate whose tag terms stood
down carries none on its card, and a row read off the card would be hidden for somebody whose
record plainly holds six. The **band is a key** and never derived from the Level, the pill's
`SCORE_FLOOR` is the matcher's own `SCORE_MIN` so a player can watch the penalty lift at the
number the engine acts on, and every absence is the field's own — no panel of noughts, and no
sentence explaining a gap.

**The card under it is headed with the rule it enforces, and one ladder tints the pill and
every bar** ([#385](https://github.com/Raketa02/Raketa/issues/385)). Three metered rows —
turning up, answering challenges and **answering about results**, never _confirming_ them,
because countering a score you believe is wrong is an answer and costs nothing
([ADR-0160](../../../docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md)) — each
printing the raw pair it was measured over, since a perfect record over nine games and one over
forty draw the **same bar**; and opponent variety as `70% · 14 of 20`, the share being the one
division this client makes and the pair being what stops it reading as a settled habit over
three games. _Counted by the system, not written by people_ is a promise about **authorship**
rather than a title, so the one strand that is somebody's opinion is dropped in `countedRows`
rather than trusted not to arrive — what other players said gets its own block, one heading
down — while `KEEPS_PLANS` and `SETTLES_UP` are kept though nothing serves them, because the
day either lights up the rows must still add to the figure above them. The tone is
`scoreTone`'s, **read twice and never written twice**: two ladders would eventually disagree and
the screen would show a green bar under a red pill for one ratio. The three fills clear 1.4.11
against their track and are told apart by lightness as well as hue, at a bound stated in `L*`
because three fills that each clear a near-white track **cannot** also be 3:1 from one another
— the arithmetic makes the third darker than black, and `meterTone.test.ts` computes it rather
than asserting it in prose. Every bar is hidden and carries no name, the fraction being text
two words earlier; and a player nothing has ever fallen due for draws **no card at all**,
because _we have not seen enough_ and _they are bad at this_ are different facts.

**What opponents said is a second block, and the heading above it is the whole reason**
([#387](https://github.com/Raketa02/Raketa/issues/387)). _Counted by the system, not written by
people_ is one star average away from false at all times, so the one thing on this sheet people
wrote stands **outside** that card under a heading naming its own author: two headings, no lie,
and the heading is the cheap half of the pair. A reader gets `4,7 / 5 · 17 players`, and **the
count is never separable from the figure** — `3,0 / 5 · 1 player` is the same field and has to
visibly read as one person's opinion, which is the raw pair's own rule one block up; the average
is written to **one decimal** through the app's single comma formatter, because `4,70` would
claim a second place nobody serves on the one figure whose design is being coarse enough to be
honest. The **subject** gets a band and no count, since an average beside a count is a
subtraction that names each new rating exactly and they know who they played — and which arm a
record carries is folded from the server's `is_self` **at the wire boundary**, so a response that
carried both draws the band and _your own record drew the figure_ is unrepresentable rather than
merely unlikely. The band **takes no tone**: `scoreTone` is this sheet's one ladder and it
belongs to the number the matcher acts on, so a coarse three-step painted in the same three
colours would offer itself to be read as a second Player Score on the one screen a held player
opens to find out what is holding them back. Both arms **carried** one sentence with two halves the contract
asks for by name — _it is not in the Player Score, and it hides nobody and holds nobody back_ —
and both sentences are now **removed** by decision, along with the band's own _a band and no
count_. What survives is the row's label naming its author; what is no longer said anywhere is
that a low average costs nothing, so a reader may take a `2,0 / 5` for a penalty the platform
issued. The sentences are kept in `recordPresentation` against the day that reading matters. And a subject nobody has rated draws **no block
at all**: a fourth absence asking a fourth question, since rating is a favour and nothing
anywhere records that a card was ignored.

**The reader's own face crosses the seam, and nothing else about the record does**
([#433](https://github.com/Raketa02/Raketa/issues/433),
[ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§3). `useOwnFace` reads the ungated `/players/me/record` and selects the photograph's signed link,
or nothing, with whether the read is in — for the yes screen, the one surface that draws the reader
as a tile rather than as a seat, because nothing carries a player's own photograph onto a court and
this is the one route that serves it. Its own key beside `detail`, and **the record's own options
whole** (`PLAYER_RECORD_QUERY_OPTIONS`): one cold read per open, no retry, nothing cached between
opens — the spec said _cached for the session_, and the link lives five minutes, so a session-long
cache would draw a dead link as a blank tile on the second yes of an evening, which is worse than
the poster; and `gcTime: 0` is what makes _no tile swaps mid-entrance_ true, since nothing stale is
there to be drawn first. `challenges → player_record` is a new feature edge, through this surface,
held open by `scripts/test-import-boundaries.sh`.

**The deck is the sheet's third door, and the header's mark gained its tick**
([#444](https://github.com/Raketa02/Raketa/issues/444),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §3,
§7). The Players deck opens this sheet from its **i** button and from a long press on the card,
with the deck's pairing in hand — subject, sport, distance, the reader's own area, the tag
overlap and `pairing: { fit, onExplain }` — so _why this Fit_ lives behind the fit row exactly
as it does from the builder's forecast card, and the deck's previous direct long-press to the
Fit breakdown is gone: a face opens the person, and the pairing's arithmetic is a row inside what
that opens. Nothing on the sheet changed for it; the props it already took were the props the
deck had. The header's `PhotoPanel` draws the on-court mark with a drawn tick before its words
now, at `space.md` down the panel rather than `space.xs`, because one mark has one drawing and
the deck card draws it too (`_shared.md`).

**The intro sits under the name, and only there**
([#445](https://github.com/Raketa02/Raketa/issues/445),
[ADR-0170](../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
§3, §4). `intro` crosses on `PlayerRecordResponse`, omitted where they wrote none and never an
empty string, and the mapper carries it verbatim — nothing trims, shortens or defaults it,
because it was fenced on the way in and is never touched on the way out. The header draws it
between the handle and the identity line, inside the drawing's own quotation marks
(`introLine`), in the deck card's role for the same line on paper instead of over a photograph
and in `muted`, because it is what they said and not what the platform measured. **Upright**,
for the deck card's reason: this app loads no italic Archivo, and a `fontStyle` on a custom
family is ignored on Android and synthesised on iOS, so the marks carry _their words_. Never
truncated — the cap at the write is what makes an ellipsis unnecessary. The header is still one
element, and `recordHeaderLabel` speaks the line inside its marks straight after the handle, so
a listener hears it as the person's own words and never as a second name. A player who wrote
none draws nothing, and the identity line closes up under the handle. The marks are spelled here
rather than imported from `play`'s `quotedIntro`: a feature may not deep-import another's copy,
and a second caller is not the third. **Present on your own record as on anybody else's** — it is
what strangers read, shown back to you — and nowhere else on this sheet or any other: not a
seat, not a Chats row, not a conversation header, not a challenge card, and not Find a game's
shortlist or pool cards, which `candidateCards.test.tsx` holds to it.

**The header draws the name, and `@nickname` under it — one of the two places a handle is drawn**
([#451](https://github.com/Raketa02/Raketa/issues/451),
[ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
§4). The record's read carries both. The title of the sheet is the whole name with `(you)` after
your own, and the handle sits under it in `tiny` and `muted` as `atNickname` spells it: two people
may share a name, and this is the screen a friend opens to tell them apart, which is why the
handle is here and on the reader's own You tab and nowhere else. The header's spoken name says
both, in the order they are drawn, because a listener is told what a reader is shown.

**The identity line prints the kilometres to one decimal**
([#461](https://github.com/Raketa02/Raketa/issues/461),
[ADR-0174](../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §2).
_In your area · 0,6 km_ for somebody in the reader's own cell, _4,3 km_ for somebody in another,
and nothing where the surface that opened the record held no distance — the same
`formatDistanceKm` the deck card and the why-fit sentence print through, so one person is one
number on all three. `distance_km` is measured between two drawn spots now, one fixed point
inside each player's coarse area, which is why a same-cell candidate carries a decimal at all;
_In your area_ is still the comparison of two codes and nothing else on the header moves. The
rule that the whole line goes on your own record stands, and so does _In your area_ standing
alone where the distance is omitted.

**The sheet has a foot now, and one surface fills it**
([#464](https://github.com/Raketa02/Raketa/issues/464),
[ADR-0174](../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §4).
`PlayerRecordSheet` takes an optional `foot` — a slot, drawn last and inside the scroll because a
sheet reads statement first and answer last (9.1), and only with the record: a refused record is
somebody the reader may not act on, and buttons over the refusal would say otherwise. It is a
slot and not a prop set this sheet reads, for the module's own rule — it reads no global state —
and what stands between two people is the caller's to know. The radar fills it with
_Not today_ · _Let's play_ or the standing relation (`radar/RadarSheetFoot`, [`play.md`](play.md));
**the deck's _i_ and the long press fill nothing, by decision**: the deck's own buttons are one tap
away and two places to answer at once invites a double tap, which `deck.test.tsx` holds. The next
surface that wants a foot has to argue for one.

**The record on the You tab — the header card, the two read-only screens, and the sheet behind
a row** ([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§1–§3). `useOwnRecord` is `usePlayerRecord` on `{ kind: 'me' }` with the id off `GET /users/me`
— the same entry the sheet reads, on the sheet's own defaults, so the card that summarises the
record and the sheet that draws it whole are one read. **`YouHeaderCard`** is the record's own
header, compact, on a dark card and one press: the name and handle from `GET /users/me`
(seeded by bootstrap, and what the _Name_ row's save writes into), the sport pills from
`GET /ratings`, and the face, the mark, the intro and the Player Score from the record — each
absent until its read is in, never a nought. The face is the panel's **`card` size (74 × 92),
not the 64 × 80 the prototype drew**: `onCourtMarkFit.test.ts` holds the mark's arithmetic for
every panel size, and a 64 pt panel leaves under 50 pt for words and a tick that need about
57, so a size that cannot carry the mark cannot be one. The score is 7.8's ring at `ringSm`
printing the bare figure with `SCORE` beneath (a Player Score is out of a hundred, not a
percentage), drawn only where the record holds a reliability. The intro is upright in the
drawing's marks, as the sheet and the deck card draw it — this app loads no italic Archivo.
**`OwnRecordSheet`** wraps `PlayerRecordSheet` on the signed-in player's id and nothing else:
no sport, no distance, no overlap, no pairing, no foot. **The two rows** are _Skill passport_
(one clause per rating off `GET /ratings`) and _Player reliability_ (`92 of 100 · 3 things
counted`, or _Nothing counted yet_ where the record has no reliability), and _How others see
you_ is a door the shell opens. **`SkillPassportScreen`** draws onboarding's `Verdict` — the
result screen's dark card, extracted so it could be — once per rating, with the sport tag and a
status `Tag` across its top (`statusChipVariant`: on-dark, amber, mint), the _Questions asked_
row left to the run, and `RecordBlocks` under each card from `GET /players/me/record?sport=`
for that sport — the score the whole person's and repeated, the run and the count that
sport's. **No ceiling tick**: `GET /ratings` serves no ceiling and this client holds no copy of
the number (7.8 as amended 2026-08-14), so `domain/passport`'s `passportCeiling` — the tick only
while the status is an Initial estimate — answers nothing until the read carries it; a constant
30 would be the copy the amendment removed. _Add a sport_ is one `Chip` per unrated sport in the
served registry — the registry minus `GET /ratings` — and not drawn for a player rated in every
sport; **a chip begins a pass of that one sport** through onboarding's `useAddASport`
([#470](https://github.com/Raketa02/Raketa/issues/470)), says _Starting…_ while the start is in
the air, and a failed start is a coral note above the chips with the chip offered again — the
player is still on this screen and a failed start began nothing. Where the pass ends is read off
its origin by the entry gate, which lands it back here with the You tab beneath; `YOU_PASSPORT_ROUTE`
is exported for exactly that caller. **The ladder** names the four bands with `bandPresentation`'s
meanings and the player's own rungs marked (_Established · you (padel)_), the rungs they are
not on at 7.5's inactive opacity, and **an edge only on a rung a served rating carries** —
band boundaries come from the response and are restated nowhere on this client, so the two
rungs the player is not on print none. **`PlayerReliabilityScreen`** is the score in the ring
at `ringLg` with the tone ladder's word beside it (`SCORE_TONE_WORD` — _Reliable_ from 90,
_Holding_ from 70, _Under the bar_ below, `scoreTone`'s three steps said) and _Out of 100_,
then `RecordCard` exactly as the sheet draws it, the sportsmanship row drawing whatever the
record serves (the band today; the figure with #473). A player with no reliability is told
there is no score and that it is not a low one, and the card is still drawn under that where
the record has a variety or an opinion. The popover for every card's three marks is one, drawn
as a sibling of the passport's root as the result screen draws its own. **Not seen on a
device**: two cards' worth of dark card and blocks scrolling, the ladder's rungs, and the ring
at 56 beside a wrapped name.

**The band left the wire before its words left this client** ([#471](https://github.com/Raketa02/Raketa/issues/471)
regenerated the contract; [#468](https://github.com/Raketa02/Raketa/issues/468) retired
`sportsmanship_band`, ADR-0179 §5). `playerRecordMappers` reads the one `sportsmanship` field for
every reader, self included, because that is the one field there is; the `band` arm of
`Opinion`, `OPINION_BANDS`, `OPINION_BAND_NAME` and `RecordCard`'s branch for them are unreachable
from the wire and stay until [#473](https://github.com/Raketa02/Raketa/issues/473) retires them
with the words and the record. The reliability screen draws the figure now, being `RecordCard`
unchanged.
