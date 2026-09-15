# plans — the plan card and the Now rail

> The design record for `src/features/plans/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The plan card is pinned under the room's header, and it is a counter, the three chips and the
lock** ([#366](https://github.com/Raketa02/Raketa/issues/366),
[#403](https://github.com/Raketa02/Raketa/issues/403),
[ADR-0144](../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
[ADR-0155](../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
**Pinned**, because a chat opens at its newest entry, so a card in the scroll is the first thing
off-screen; **no panel**, because the panel that explains the chips is the game screen's — one
panel, one home. `domain/slots.ts` is the one place `where · day · hour` is an order, and the order
is of decreasing negotiability. **The count and the lock are two facts, and `domain/lock.ts` holds
both**: `N of 3 set` is derived from the three fields and never sent, and `Locked` is `lockedAt`
and **never** the count under another name — three filled slots is a plan everybody _could_ agree,
and the lock says somebody did, by posting `{name} locked the plan` into the room, which is the
whole of what it does. _Lock the plan_ is greyed below three, live at three, busy with its own word,
and **gone** once locked rather than 6.1's `settled` — a second lock records nothing and answers
`200`, so a control still offering it would be one that provably does nothing, and the counter's
word is the carrier. **The label carries no reason**, because the counter directly above is the
note #324 owes every greyed control. **A lock freezes nothing and there is no unlock**; `locked by
everybody` stays a phrase the data cannot support. **A hold met on any plan write reaches the
room's one amber note** off the mutation cache, through `usePlanWriteRefusals`, because a hold is
a fact about the account whichever of the five writes on that screen met it. **Two grids and
neither is a rule this client invented** — the day row is today + 6
clamped to `planned_at + PLAN_HORIZON`, so it **shrinks as the week runs out** and inside the entry
grace draws **no chips at all** with the refusal sentence beneath them, and the hour row is the
thirty-five half hours between 06:00 and 23:00; both numbers are the server's, which refuses
`the_day_is_past_the_horizon` and `the_hour_is_not_offered`, and _the grid a client draws is a
convention, and this refusal is what makes it true._ **A past combination is refused in written
copy rather than by a disabled control**, because the day and the hour are filled in either order
and either can be the second — so the sentence names **both** remedies, names no value, and is
drawn under the row with both chips above it. **Nothing here is optimistic**: a slot change writes a
line other people read, so the chip goes **busy with the value it already had** and the new one is
drawn only once the server has answered — which is why 6.2 grew 6.1's `busy`, label swap included,
since this system greys for _you may not_ and for _on its way_ alike and only a word tells them
apart. **The line arrives through the stream like any other entry**, on the same nudge every other
member's copy of it arrives on, so nothing in `plans` invalidates the room — **and the room's nudge
re-reads the plan and the game beside the stream** ([#405](https://github.com/Raketa02/Raketa/issues/405),
[#406](https://github.com/Raketa02/Raketa/issues/406)), so the card, the quick chips and the
header's state word say on every phone what the line says, with nothing pressed, and a court that
completes while the room is open draws its card there and then; on every nudge and never on
sighting a plan line, because a trigger keyed on the line vocabulary goes stale on exactly the
build too old to read a new code — _a nudge re-reads what the room draws, and nothing it does not_,
which is the Chats list. Every plan write first **cancels** the plan list's in-flight read, which
is not optimism — a nudge-started read can land after the reply that was written in, and would
roll the slot back for a second; the games list needs none, because a result write invalidates
rather than writes in. **Any member may fill
or change any slot, any number of times** — the line is the friction, there is no rate limit, and
**a slot is never emptied**, so every editor opens on whatever is there and none of them offers a
way to clear one. **The card is folded against `GET /games`' `read_at`** and never against the
phone: `GET /plans` deliberately carries none, because a plan folds nothing against the clock, and
_today_ and the horizon coming off one read is what makes `today + 6` and `planned_at + 7`
comparable at all. **`features/plans` may import `features/games` and never the reverse**
([ADR-0149](../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §1) —
the client half of ADR-0145 §4's clause, and _a grep rather than a judgement_: `eslint.config.mjs`
refuses the import in three blocks, one per baseline block it shadows, and `pnpm test:boundaries`
drives all three plus the two exemptions they could silently have dropped. The room composes the
card, which is the shape #364 anticipated as a slot the route would fill and this ticket did not
take: the game id comes off the read the screen mounts and `held` off the fold below it, so a slot
would have been a render prop over a route that had joined the room itself — three props and a
second join to avoid one import through a public surface the room already makes to `features/games`
for its _Details_ door. The same read answers the quick chips, which is the `undefined` #364 left
them holding — **and the chips' rule and words moved here with it**, because §22.4 is the plan's
vocabulary by `the-words.md` §22's own assignment and the rule reads the slot order. #364 declared
its own `PlanSlot` and its own order to make do with no plan feature to put them in, and a second
spelling of _where · day · hour_ is exactly what this ticket says `domain/slots.ts` must be the one
place of. **The row stayed in the room**: a chip is a message, and the send it goes out on is the
composer's — and since [#402](https://github.com/Raketa02/Raketa/issues/402) it is drawn **inside
the composer's block**, one surface with the field and a coral Send under one hairline at the foot
of the screen, on the screen's own `paper` because the bottom inset is the frame's under it. **The platform zone left `conversations`** for `shared/date/platformZone.ts` on the
third-caller rule, and unlike the tables promoted before it a second copy would be two answers to
_which day is it in Warsaw_ on one screen; #335's _shorter value, not a second line_ moved to
`shared/formatting/placeName.ts` beside them, because the `Where` chip is the third surface that
rule governs.

**Now stops being a placeholder, and what replaces it is a rail, a ladder and nine card states**
([#367](https://github.com/Raketa02/Raketa/issues/367)). `PLACEHOLDER_COPY.now` is dead and
`shellCopy.test.ts`'s _never says nothing is happening_ **moved with the copy rather than being
deleted** — it was Now's refusal first. The tab keeps the shape it has always had: it owns its own
sentences and nothing drawn under them, and the sentences are handed to `GamesRail`, which is
`features/plans`' because a card needs a **plan** beside a **game** and ADR-0149 §1's arrow runs one
way. **They are not gated on the read having landed**, and that is the point of how §22.7 worded
them: _every game you arrange shows up here_ and _Play finds you one_ are true of a player with five
games and of one with none, so there is nothing to hold them back for and holding them back would
leave a blank screen. The bolt is not drawn, on 10.2's own rule.

**The ladder is `domain/`, five rungs read in order, and the clock outranks the checklist** — _a
seat is open_ → Needs a player, _the agreed point has passed_ → Needs result, _the agreed day is
today_ → Today, _all three slots filled_ → Game on, otherwise Planning. It is the single most
drift-prone thing on the map: five card names, two tickets that each keyed a rule on it and one
amendment already spent closing the hole between them, so it is one function every surface reads. The **agreed point** sits beside it — the
agreed instant when day and hour are both recorded, the start of the following local day when only
the day is, nothing when no day is, **later rather than earlier** so nobody is asked for a result
before they could have played — and it is the server's field, never recomputed here. Everything
folds against `GET /games`' own `read_at`, so **Now has one clock by construction** rather than by a
rule anybody remembers: `GET /plans` deliberately carries none.

**A rail, not a list.** `GamesSection` refused shelves in writing and a rail keeps that refusal by
not being a list at all — a heading with a count, one card, a swipe, and nowhere to put a shelf. The
card is 7.7's **paging** geometry at the content width, so it has **no peek**, which is what makes
7.18's dots the affordance rather than decoration: they **track the scroll**, they are not
pressable, and they say nothing, because the count is on the heading above them. The order is **the
server's — newest arrangement first — and stable**, where a clock sort silently re-orders a player's
cards between sessions; the cost is stated rather than hidden. **Endings keep a card for 24 h and
then leave**, measured from the last instant the wire dates on the game, which is exact for one that
never happened and early by at most one answer window for one that was played.

**The card is tag · eyebrow · figure · line · gloss · court · footer, and every name is folded at
read time** — no client state machine and no status column. The tag **is** the card's name and its
dot is the **sport's**, with urgency carried by the whole pill; a standing this build cannot read
draws **no tag**, because there is no name to say and the gap belongs in the line the standing
_is_. The figure takes **three shapes** — the hour, the weekday when there is a day and no hour,
nothing when there is no day — and the line takes whatever it did not, which is what keeps **the
hour printed once**. The gloss is **one rule for three rungs**: the next unfilled slot in slot
order, with _Needs result_ overriding it with the time left, so there is no fourth string to keep in
step with the ladder — and everything that is not a rung already has a sentence, `features/games`'
`gameStandingLine`, the same one the screen behind the card says. The court is 7.12 at `header`, and
its seats are **generated posters plus 7.12's three-character caption** — the caption moved to
`seatFace.tsx` when a third court needed one — with the unknown player's `?` for a seat `users` can
no longer answer for.

**The footer is a named door and the ✉, over 7.7's `marginTop: auto` hairline**, which is what
aligns footers across cards of unequal height and the whole reason a rail can hold a 40pt figure
beside none. **The button is a named door**: it carries the act's verb, it navigates, and it
**never writes** — and the body goes wherever it goes, so the two are one action and one
accessibility element whose name ends with that verb, which is why the drawn button is hidden. The
✉ is the second element because it goes somewhere else, and it is drawn only where there is a room:
the join fails soft, and an ending destroys a conversation rather than delisting it. **The ✉ is
Feather `mail` and never the character**, on the bolt's own argument — Archivo ships no U+2709.
A game is genuinely **pushed** over the rail, which made it the first screen outside Play to take
the shell's push transition and the first to need `shellTabs` to say which tab a segment is
_inside_ — Now's root is `/`, so a screen over it cannot share its segment the way the builder
shares Play's. Neither write on the screen behind it is optimistic and neither overrides
`networkMode`: a standing is folded from the record and the clock, so the only client that can be
right about what a game becomes is one that asks, and the app's own test — _does this act carry a
deadline the player chose?_ — answers no for both, where the challenge send answers yes.

**The Now card is a dark shell — a stage chip, the sport word, three slot rows with a bright-or-dim
bar, a bigger court with faces, and two doors — and the Planning card is the first one drawn for
real** ([#413](https://github.com/Raketa02/Raketa/issues/413), the design of
[#410](https://github.com/Raketa02/Raketa/issues/410), which wins over every record it disagrees
with and has each of them amended). One `GameCard` still draws all nine names and branches on
nothing: every slot that differs by name is a table lookup in `nowPresentation.ts` — `CARD_TAG`,
`STAGE_DOT`, `ACCENT`, `doorLabel` — so a tenth name fails `pnpm typecheck` in one file, and every
name but Planning is drawn on **soft defaults** (mint bars, a mint `settled` door, the stage dot as
the table says) until its own design arrives, so the rail does not mix two visual languages and a
game flipping to _Game on_ under a thumb does not jump layouts. **The dot is the stage's** and the
sport is the word beside it — the one surface on which a `Tag`'s dot is not a sport's, legal
because the sport left the dot for a word and the token has one meaning on the card; nothing
writes _singles_ or _doubles_, because the court says the format. **The figure, the line and the
gloss retired into three `SlotRow`s** in `slots.ts`' own order: a settled slot draws its value big
and white under a bright bar — the place without its court, `Sunday` `9 Aug` (the first date this
app draws, §5.4 #6 amended), the hour in mono — and an unsettled one draws `Not agreed yet` small
and grey under a dim bar, so the card fills with brightness as the plan does; `Not agreed yet` was
the chips' spoken word only and is drawn now, capitalised, from one constant; `TIME` is the card's
word for the `hour` slot where the chip keeps `Hour`; every value box is `h2`'s line tall so the
bars stand at one height whatever they hold. The settled bar is the third drawing of
`size.semanticBar` — bright is agreed, dim is not, on dark only — and the bright colour and the
wide door's variant come from one `ACCENT` row, `volt` on Planning (_the plan is settled here_, a
meaning volt has on this card and nowhere else, off `primary` still) and mint elsewhere, on 6.1's
`settled` rather than a `mint` variant that would have equalled it. **One line survives under the
slots** so no card loses a fact it drew: _Needs result_'s window and the endings' `gameStandingLine`.
**The court is `court.card` 88, measured against mock 1 at 1×** and not derived — a 21pt seat by
the ratio, which is what the mock's tiles measure — with **a face in every seat where the room has
one**: the conversation rows the rail already fetches for the door carry every member's `photoUrl`,
so `useChatDoors` folds `faces` beside the `conversationId` under the same challenge key and the
card is handed both, failing soft twice over — no room is no bubble and posters in every seat, and
no new fetch. **The caption is three letters on every seat, yours included**: the `volt` ring is
the mark, and `you` under a ringed face was the same fact twice; every seat is handed to `SeatFace`
as a `player`, because the `you` occupant exists for a builder that cannot carry your photograph
and here the room does. No sport caption on the ground, because the sport is the word in the
header. **The body is not pressable** — the two buttons are the only doors, which reverses §5.2's
_the card body goes wherever the button goes_ — so the body is one accessibility element with no
action, named for the tag, the sport and the three slots as sentences in the read-only plan tags'
own shape, and the wide door's verb is no longer in that name because the door is an element of
its own now and a name ending in `Open` beside a button announcing `Open` is the double announcement
6.8 refuses. **The wide door is the next thing to do**: `Finish the plan` on Planning — the same
`open` door as Game on's, under the word for the errand, and _Finish_ rather than _Lock_ because
the lock is an act with its own control on that screen — `Open` · `We played` · `Confirm the result`
on the others, and none on an ending; `doorLabel` is keyed by the card's name rather than by the
door for exactly that reason, and a test holds it in step with `domain/`'s `DOOR`. **The
consequence is stated: an ending's card opens nothing**, and the room behind it is destroyed, so a
finished game's screen is not reachable from the rail — the card is the record for the day it
stays. **The bubble is the app's first icon-only button** (design-system 6.14): Feather
`message-circle` on `onDarkFill`, `minTouch` wide and `btnLg` tall so the row reads as one, with
`Open the chat` spoken always and the glyph hidden; `Button` still has no glyph slot. The footer
has no hairline — the design draws none, and a fold between the slots and the door that finishes
them would cut the card in two — so the row itself takes 7.7's `marginTop: auto`, and `doors={false}`
draws none at all — no caller yet; it is the prop #414 will draw the shell with at the top of
the game screen, where both doors go. **The stage dot's
colour was measured and found to be `amber`**: mock 1's dot is `#87641A`, a degree off amber's hue
and a step off its lightness, at 1,61 against the tag it sits in — the value the ticket itself
calls invisible on `night` — so `color.arranging` keeps the mock's hue and saturation and lifts the
lightness alone to the step past the first that clears 1.4.11 on the tag's ground (`#D29B28`: 5,35
on `night`, 3,49 on the tag, 3,17 on the icon door), named for its meaning — _a stage still being
arranged_, the plan before the game and the result after it — and both the refused value and the
drawn one are computed in `Tag.test.tsx`. `domain/` is untouched: the ladder, `gameCardName` and
`DOOR` are what they were. No device has drawn any of it; the three Planning mocks are the fixtures
`nowRail.test.tsx` walks, and the card is asked for a look against them.

**The game screen's plan lead draws the chat's editable card, with the panel inside it, under the
Now card with its doors left off** ([#414](https://github.com/Raketa02/Raketa/issues/414), the design
of [#410](https://github.com/Raketa02/Raketa/issues/410), which wins over
[ADR-0149](../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
§4 and has it amended). `GameScreenWithPlan` fills three slots now rather than one — `card`,
`court`, `plan` — every one an opaque `ReactNode`, so `features/games` still never learns a plan
exists. The **card** is `GameCard` with `doors={false}`, on the same `useChatDoors` join the rail
runs — the room's address it does not draw and the faces it does, keyed by the challenge, failing
soft into posters — and with no `width`, because a column child takes the content width where a
horizontal scroller's child has to be told it (Part 16). The **court** is `features/games`' own
`CourtPairing` ([#415](https://github.com/Raketa02/Raketa/issues/415)) — the pairing ADR-0161
admitted, drawn by the feature that owns the read and handed the same faces map, because the
players card draws the same people off the same join. The **plan** is `GameScreenPlan` on the plan lead and `GamePlan` on
the score lead, decided beside the lead itself so the two cannot disagree. `GameScreenPlan` is
`RoomPlan`'s shape one surface over — `PlanCard` **reused as it is**, handed the game's own clock
— with two things the room does differently: `PLAN_PANEL` is drawn **inside the card through the
`note` slot**, between the chips and the lock, where the design puts it and the room leaves empty,
so _no panel in the room_ stays true and the panel still has one home; and `refused` is folded
here off the same mutation cache the room reads, through the room's own `writeStanding`, with the
room's own sentence drawn once above the card as an `alert` — one fold and one constant, because
a hold is one fact said on two surfaces, and a greyed chip with no note would be the dead end #324
refused. **Why the editable card and not the tags**: #413's wide door on the Planning card says
_Finish the plan_, and a screen that answered that verb with three tags and a door back to the
room would be a screen that did not keep what the button promised; the room is still where the
arranging is _seen_, since every write posts a line into it. **Where the card sits is the
surface's to say**: `PlanCard` lost its gutter margins, `RoomPlan` pins it at the gutter in a
wrapper of its own as before, and the game screen lays it in a scroll that already is. The read-only tags,
the checklist and `GamePlan`'s chat door **stay for the score lead**, where the plan is context for
a score and _a control that cannot be operated must not offer the affordance of one_ still holds.
Two of §5.4's corrections are re-decided by the design on this lead and one is not: a lock word
**is** drawn (greyed below three, as the chat decided it — never _set all three first_), a date
**is** drawn (on the card at the top, beside the weekday; the chips keep the weekday), and
`competitive` still is not. No device has drawn it; the screen is asked for a look against mocks
4–6 and 9.

**The open seat outranks the clock, and the ladder gains a rung above it**
([#418](https://github.com/Raketa02/Raketa/issues/418), the third child of
[#411](https://github.com/Raketa02/Raketa/issues/411),
[ADR-0162](../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)). A seat
somebody left is `player_id: null` on the wire and `playerId` absent on `GameSeat`, and the mapper
**keeps** such a game — the seat keeps its place and its side, the court keeps its size — because
dropping the seat would publish a three-person doubles game and dropping the game would take a
live court off the rail. `rungOf` now reads the court as well as the plan and the instant
(`CourtRead`, the two fields of a `Game` the ladder needs), and _Needs a player_ is read **first**:
a game with a gap in it cannot be played or recorded until somebody is in that seat, so _Needs
result_ over a short court would ask for a score nobody could enter and _Today_ would announce a
game that has a gap in it; the server's own `NEVER_PLAYED` still wins, because a window that
closed on a short court closed all the same. Nothing on the wire names the rung — the standing
stays `AWAITING_ENTRY` and the seat says `null` — so the ladder is the one place the two are read
together, and the rule is spelled on the field there rather than imported from `features/games`,
on `gameCard.ts`'s own `import type` line. **The tables gain a row each**, on the shell's soft
defaults: the tag `Needs a player`, the stage dot `arranging` (the game is back in the players'
hands), the accent mint, the state word `needs a player` for the room's header, and the door
**`Open`** — the same `open` door as _Game on_'s under the same word, until
[#419](https://github.com/Raketa02/Raketa/issues/419) turns it into _Fill the seat_, because no
dead door ships. **The court draws the seat empty, and it is the builder's empty seat**:
`SeatFace`'s `empty` occupant under Play's dashed `empty` ring with no plus in it, no caption and
no `yours` ring — `CourtMini` draws an unfilled seat as nothing, and the reason does not
transfer, because that court's summary says how many seats are filled and this card names the
errand and draws the seat the errand is about. **The card's spoken name gains one clause** after
the sport — `An open seat` · `2 open seats` — because the court is hidden from a listener and the
tag names the errand and not the shape. **`entryLeadOf` takes the court** and is still derived
from the card's own door, so a short court leads with the plan whatever the clock says — a seat
open is not a score to enter — and **`momentHasPassed` is exported** from the ladder, the first
clock rung's own test, for the one control drawn only while the moment is ahead. **The game
screen's plan lead gains a fourth slot, `courtActs`, drawn last under _We played_**, and this
feature fills it with `features/challenges`' `LeaveGame` — a challenge act reached from a game,
composed here exactly as `useChatDoors` is, through that feature's `types.ts` — **only while the
agreed moment is ahead**, mirroring the rule the server enforces with `game_moment_has_passed`;
the rung alone cannot say it, because _Needs a player_ outranks _Needs result_. On a stale tap the
control asks this composition to re-read the games list, because that read is the one clock every
fold on the screen is against. **`CALLED_OFF` is absorbed as far as the compiler forces**
([ADR-0163](../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)): the fourth end
gets its name, `called-off`, and a soft-default row in every table — `Called off`, the hairline
dot, no door — and nothing more; its `called_off_at`, its shelf life and its screen are #419's,
and until then a called-off card stays on the rail, as every undated ending does. No device has
drawn any of it; the rung, the empty seat and the control are asked for a look.

**The reopened court's door is the fill, and the fourth end gets its shelf life**
([#419](https://github.com/Raketa02/Raketa/issues/419), the fourth child of
[#411](https://github.com/Raketa02/Raketa/issues/411),
[ADR-0163](../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). `GAME_DOORS` gains
`fill` and _Needs a player_ carries it: the card's wide door on that rung is `Fill the seat` — the
challenge screen's own fill, run from the card and landing in the builder under the challenge —
and it is **`features/challenges`' `FillTheSeat` drawn in the door's place**, with the card's
accent and the door's width, rather than a button here that knows what a fill is. The card hands
it the game's `challengeId`, its sport, the people the game's seats hold (`seatedOthers`, read off
`features/games` beside `openSeats`) and one rule, **only while the agreed moment is ahead** —
`momentHasPassed` off the plan and the games list's instant, the same test the leave reads —
because nobody may be seated into a game whose moment is gone; past it the card draws the bubble
alone rather than a door whose send would be refused. The word is `theActsWords.ts`', for
`WE_PLAYED`'s reason: two features say it and the control is composed into the card, so it can
live in neither. `GameCard` gains `onReRead` for the one refusal that is a re-read, handed the
rail's own games read. **The game screen's `courtActs` slot now holds three**, in the design's
order: `FillTheSeat` as the arm's primary act where _We played_ would be, `CallOff` above the
leave, `LeaveGame` last — each handed its one rule as `offered`. This composition states what is
its own to state — a seat is open (`openSeats`), the moment is ahead — and **never learns what an
organiser is**: `CallOff` joins that fact off the challenge list itself. **`Called off` is finished
on this side**: `belongsOnTheRail` reads `calledOffAt` first, because `entry_closes_at` is `null`
on it and `played_at` never is, so the card is shelved a day from the act; the tag, the hairline
dot and the state word were #418's, and the line under the slots is the standing's one word. The
card's door and the screen's acts have not been drawn on a device; asked for a look, and for a
words decision on the ending card, whose tag and line both read _Called off_.

**The plan is the challenge's, the card is pinned from the room's opening, and the lock waits for
the court** ([#425](https://github.com/Raketa02/Raketa/issues/425), the client half of
[ADR-0164](../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md),
spec [#420](https://github.com/Raketa02/Raketa/issues/420)). `Plan` is keyed by `challengeId` — the
one id a room and its game both carry — and gains `anchor`, the instant the day row runs from: the
challenge's send until the game exists, then the game's `planned_at`, sent on the row rather than
derived because a room with no game has no `planned_at` to derive it from. So `offeredDays` takes
`{ readAt, anchor }`, _today_ is **the surface's own instant** — the room's `read_at` in the chat,
the games list's on the game screen — and the row a half-built court offers is shorter than the one
its game will and **widens** when the court fills, never the other way. `GET /plans` lists **one
row for every court the reader holds an accepted seat on, written or not**, so a row with three
nulls is the ordinary opening of a room and _no row_ means the list has not landed or the reader
holds no seat; `PlanCard` therefore takes a `Plan` and never `undefined`. **The two surfaces read
an absent row differently, and the difference is where the anchor can come from**: `RoomPlan`
draws nothing until the row lands — a room without a game has nothing to derive the anchor from,
and the row is what says there is a card to draw — while `GameScreenPlan` draws the card off the
game's own `planned_at` in the meantime, which is exactly what the row's anchor is once a game
exists (§4), so the game screen keeps the loading state it had: three empty slots, the held note
and the panel, from the first frame. The four writes are addressed by the challenge, `usePlan`
looks a court up by it, and the rail and the composed game screen join a game to its plan by
`game.challengeId` — so a court whose four people filled every slot in the chat lands on Now as
_Game on_ on its first read, never as _Planning_, and Now still draws nothing for a court that is
not whole (ADR-0164 §7). **`lockControl` gains a fifth state, `waiting`**, read before the count
off a named fact rather than an optional count: the card is handed the court's **`LineUp`** —
`{ complete: true }`, or `{ complete: false, members, seats }` — and while the line-up is
incomplete the button is **absent, not greyed** (#324), with one line in its place,
`lockWaitsLine` — _2 of 4 in — you can plan now, lock when everyone's here_, the room's members
over the sport's seats. **Complete means the court has become a game, never that the count is
full** (ADR-0165 §1: _has this court become a game_ is the line-up having completed), so a game a
seat has since been left open on is still complete and still draws the button. The room folds its
line-up in its own `domain/room.ts` (`lineUpOf`), because it alone holds the members and `gameId`,
and is handed the sport's seat count by the screen, because how many stand on a court is
`shared/ui`'s drawn knowledge; the game screen hands `LINE_UP_COMPLETE`. This feature decides only
that a court still being filled has no lock to draw. A singles room never
draws the line: two yeses is the whole court, and the room opens with its game. The line becomes
the button on the nudge that brings the game, over the slots recorded before. A game a seat has
since been left open on still draws the button, and the server's `the_court_is_not_whole` is
surfaced in words — _Not everyone's here yet — lock the plan once they are_ — rather than
pre-empted. The count line is a sentence with two numerals in it and is drawn as one, `tiny` and
`muted`, as _you need 2 more_ and _8 days left_ already are: the mono-and-tabular rule is for
figures that stand alone and would ripple. `GamesRail` and the ladder are otherwise untouched. No
device has drawn the count line; it is asked for a look.

**The court's ground is clipped to its radius and the seats are not**
([#429](https://github.com/Raketa02/Raketa/issues/429)). At `court.card` the near-right seat of a
doubles court stands at 110 of 132, and the three letters under it end six points past the
court's bottom edge — with the clip on the court itself they were drawn cut through the glyphs, on
the one seat of four. `Court` now clips its ground layer alone; a seat is the caller's child that
the court only places, so the caption hangs where the geometry puts it, onto the card's own
`night`, which is the colour the ground ends on. No number changed. No device has drawn it since;
it is asked for a look.

**The day row says _Today_, and no card does**
([ADR-0166](../../../docs/adr/0166-the-day-row-says-today-and-no-card-does.md)). The ladder is
**four** rungs now — _a seat is open_ → Needs a player, _the agreed point has passed_ → Needs
result, _all three slots filled_ → Game on, otherwise Planning — and the calendar is not one of
them. ADR-0145 §3's _the agreed day is today_ → Today, above the checklist and since #324's second
amendment needing no hour and no place, named a card after the day rather than after what the plan
had reached: a day-only plan on the morning of its game drew a settled tag, a mint dot and
_We played_ over a dim `TIME` bar, and the same plan a day earlier drew Planning. The day was
already on the card — #413's day row prints `Monday` `14 Sep` — so the tag was that fact said
again in the one slot meant to name the stage. What §3 bought, _a plan makes the clock drawable_, is
kept and moved: `SlotRow` draws **`Today` `14 Sep`** in place of the weekday when the plan's day is
the platform day of the games list's `read_at`, and speaks it the same way. The test is
`dayIsToday` in `domain/slots.ts`, defined **once** and read twice — by the day row through
`planPresentation.ts`' `cardDay`, and by `quickChips.ts`' _On my way_, which had its own copy of
the comparison; `spokenSlotValue`'s `{ date }` option became `{ readAt }`, because the card is now
the one surface that draws the date **and** the one that says the day has come, and both come off
the same instant. **Only the card, and only _Today_**: the room's chip and the game screen's tag keep
the weekday (a chip saying _Today_ in a row of `Mon Tue Wed` is a different kind of word, and the
chip opens that row), and there is no _Tomorrow_ or _Yesterday_ — this folds a state into the day
row, and _Tomorrow_ was never a state. The one thing a player notices: **_We played_ leads only once
the agreed point has passed.** A game on its own day reads `Open` or `Finish the plan` and lands on
the plan lead, where _We played_ is the quiet door under _Open the chat_ exactly as on any other
day; a Game on card that led with _We played_ when the day is today would be the Today state under
another name. `CARD_TAG`, `STAGE_DOT`, `CARD_STATE_WORD`, `ACCENT` and `DOOR_LABEL` each lost a
row in one commit, `nowPresentation.test.ts` holds the name absent by name, and the backend's two
transcriptions of the ladder (`app/seeds/loop.py`, `tests/api/test_the_loop.py`) dropped the rung
with the client — the seed's _Today_ fixture now reaches Planning on the day of its game, which is
the card this record is about. Nothing on the wire moved. No device has drawn the row; it is asked
for a look.

**The called-off card offers two things and names nobody**
([#454](https://github.com/Raketa02/Raketa/issues/454), [ADR-0172](../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§5, §8). `DOOR['called-off']` is `open` — _What happened?_ (`WHAT_HAPPENED`) in the on-dark fill,
the tag's own quiet colour, opening the game screen whose heading says who — and `cardLine` says
nothing under its slots, because the tag is the whole of what the card says. Beside the door, where
a live card has its bubble, the **trash**: `features/games`' `RemoveCard`, composed here as
`FillTheSeat` is, on the one card `mayBeCleared` names — a `Record` over `GameCardName`, so
widening the trash to _Never played_, _Counted_ or _Uncounted_ is a row and a decision, which the
record names out of scope. The card leaves the rail on the dismissal's reply and no sheet stands in
front of it; a refusal is that hook's own re-read of the rail and says nothing — unlike the fill,
the act lives beside the list it touches, so the card hands it no `onReRead`. `ACCENT['called-off']`
is the one row whose button is not `settled`: a green door under a red tag would be a card whose
colours disagreed about it. **Not seen on a device** — the action row is asked for a look.
