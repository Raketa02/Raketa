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

**The ladder is `domain/`, four rungs read in order, and the clock outranks the checklist** — _the
agreed point has passed_ → Needs result, _the agreed day is today_ → Today, _all three slots
filled_ → Game on, otherwise Planning. It is the single most drift-prone thing on the map: four card
names, two tickets that each keyed a rule on it and one amendment already spent closing the hole
between them, so it is one function every surface reads. The **agreed point** sits beside it — the
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
