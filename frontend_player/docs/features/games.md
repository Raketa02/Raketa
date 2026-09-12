# games — the result argument and the game screen

> The design record for `src/features/games/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The result argument is one screen and eight states, and the state is derived**
([#314](https://github.com/Raketa02/Raketa/issues/314),
[ADR-0137](../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)). **A result is the
record that a game happened** — no booking, no calendar, no date field anywhere — so the entry
_is_ the fact, and everything after it is an argument bounded to two rounds —
`domain/resultArgument.ts` is named for it, because the glossary word _conversation_ belongs to
the room the first acceptance opens, and two of them in one codebase is how somebody eventually
subscribes the wrong one. It folds the standing, the scores on the table and **which seat is
yours** into what to draw, and nothing outside that file reads a `GameStanding`: a
**correction** and a **counter** are the same `POST` and completely different news, and #314's
own worry is that _"a player will spend an attempt fixing a typo."_ Three of the eight are worth
knowing. **Silence confirming is drawn before
it happens**: the standing line says it **on the row as well as on the screen**, so a deadline is
never something a player reaches by tapping, and the screen adds
`prototype/result-confirmation`'s clock block over it — a figure at arm's length above one
sentence. **`both-stand` draws both scores and offers the agreement that ends it** — ADR-0137
§4's only exit short of the game going unscored, and the one the screen could not offer while
`standing_proposal` was _"when exactly one is"_ and the wire returned **neither** score
([#317](https://github.com/Raketa02/Raketa/issues/317),
[#318](https://github.com/Raketa02/Raketa/issues/318)) — the **eighth** state is the agreement
itself, below. The reader's own score is drawn quiet
above the other side's, the one control is named for the score it agrees with, and the copy names
the way out instead of stating an ending as though it were the only one. There is never a counter
there: that side has had its one turn. **Which of the three `AWAITING_ANSWER` screens it is comes
off the count** — `proposals` carries nought, one or two — rather than off an absence that used to
mean _nothing entered_ and _both sides have spoken_ alike. And **an agreement is a state of its own rather than a flag on the three it can happen in**: for
the length of the grace the standing still reads `AWAITING_ANSWER`, but the proposing side has
stopped waiting on silence, so the headline and the clock say the score was agreed and when it
settles, the correction goes (`state_result` refuses it with `the_other_side_has_answered`, whose
sentence can now say _while this screen was open_, because the control's own absence is what
proves the timing), a second agreement from the same side goes with it, and **the disagreement
stays** — inside the grace a counter still beats an agreement, which is the whole reason the
grace exists. It is an arm rather than an optional field because carried as a field it was a
state every renderer had to remember to pre-empt its own `switch` with, and the one that forgot
said something false. It **keeps both proposals**, because what is left to do is read off them:
the side that may counter is the side that has not spoken, and two scores standing means neither
can — the aggregate's one-per-side cap rather than a rule this client invented.

**The instrument is the prototype's, and so is most of the copy.** #314 says the score-entry
interaction is solved work, and it is: a **pad** over a grid of the sport's own legs, both sides
named above the columns they own, because _"`6-4 3-6 6-2` is not a score until you know whose 6 it
is"_ and a stepper is six taps to reach 6. The **`+` key** beside it is what keeps the range
honest — a padel third set is often a ten-point tie-break and a badminton game goes to thirty — so
_we know the shape, not the rulebook_ is built into the instrument and not only into the
validator. Variant C's layout comes with it: the score being answered stays on screen **beside**
the one being typed, and an unscored evening ends on a fact list rather than an apology. Two
things are rewritten because the model moved. **There is no absolute time anywhere** — the
prototype quoted one beside every duration, and this platform has no calendar to print one
against — so every span is measured from `read_at`, the instant the standing beside it was folded.
And **a person is named where a person acted, and a side where a side did**
([ADR-0141](../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). A seat carries
a handle and nothing else about the person in it — no Level, no band, no run of form, because a
card is what a _searcher_ reads to decide about a game that might happen and this is the record of
one that did. So the eyebrow says **who you played**, which is what tells two padel games in a week
apart, and _tomek.p put a score up_ and _tomek.p agreed with your score_ name the person a result is
being settled with. The score's two columns stay _You / Them_ and _Your side / Their side_: a score
is a **side's** claim, capped one per side and answerable by either of the two who played it, so a
column headed with a handle would charge a doubles score to one of them. Every handle is drawn
**whole**, which is
[ADR-0107](../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4, and a seat
`users` can no longer answer for draws the unknown player's `?` rather than being dropped. The
prototype's `✓` went the way the on-court mark's did — **Archivo ships no U+2713** — and the
winner's row carries the word instead.

**One screen shows a game whatever state it is in, and the plan arrives on it as a child**
([#368](https://github.com/Raketa02/Raketa/issues/368),
[ADR-0149](../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §2).
**Grown, not replaced**: `GameScreen` was already a state-keyed detail surface with ten arms, and a
hand-off in the middle of one standing's life would give a player two different screens for the
same game depending which day they tapped it. What it grew is **one `ReactNode`** and **one word**,
and **`features/games` still never learns a plan exists**: no `Plan`, no ladder, no rung, and
`eslint.config.mjs` refuses the import. `GameScreenWithPlan` is the one place that holds both
halves — it does the join, folds the arm and fills the slot — and **both routes mount it
unchanged**, so a composition spelled at two call sites cannot drift at one of them.

**`AWAITING_ENTRY` is one standing over two landings, and that is the arm.** §5.2 lands _Planning_
and _Game on_ on **the plan** and _Today_ and _Needs result_ on **the score grid**, so the grid is
the screen on the two arms the moment has reached and **one press away** on the two it has not —
the press being `We played`, one word in `shared/vocabulary/theActsWords.ts` that the Now card's
door reads too — shared rather than either feature's, because the two reach each other at load time
and a word read across that seam mid-evaluation reads a half-built module. The word that crosses back into that feature is `EntryLead`, in its own
vocabulary rather than a rung in somebody else's, and it is **derived from the card's own door**
(`entryLeadOf`) so the two tables cannot disagree about where a button goes — _the verb names what
you arrive at_. **_We played_ is available on every entry arm**, not only the two that lead with it,
because `standing_of` gates entry on `entry_closes_at` alone: four people can arrange a game at six
and play it at eight without filling a slot. The cancel follows from the same fact — a grid that
_is_ the screen has nothing behind it to go back to.

**The child is the plan read rather than edited** — `Tag`s and never `Chip`s, one accessibility
element, with §22.2's **inverted** panel over it: it stops explaining an absence and names one,
because a player seeing _Zabłocie Sport · Saturday · 18:00_ inside an app may reasonably assume the
app did something about it. **The checklist is three lines, capped, in one order**, and its third is
**cited, not written** — `worthLine`, the whole of what survives ADR-0143 §8's refusal — so the
screen defers its own copy of that sentence on the entry arm rather than printing it twice. What the
arm changes is **the screen around the child and nothing inside it**: §22.6 settles that _the rungs
differ by the clock and not by the arrangement_, so the checklist is one rule on all four and no arm
reaches the child at all. **A plan arm asks for nothing, so nothing on it wears the one accent** —
the chat door is 6.1 `secondary` on every arm, because an accent in the scroller beside a quieter
control in the pinned slot inverts what pinning is for, and the coral comes back where
`Send this score` is pinned. **_Open the chat_ is always drawn, whichever door you came in by** — arriving
from Now it is the point and arriving from _Details_ it is the way back, so drawing it conditionally
on the route would make the surface depend on its door; it fails soft on the room being gone and on
nothing else. **One component, two routes** — `/games/[gameId]` and
`/chats/conversation/[conversationId]/details` — so each lights its own column and _back_ is correct
by construction, with **no `from` parameter** and `tabForPathname` still pure. Eight corrections to
the details design are **absences** rather than sentences and each is a record read out in
`GamePlan`'s own note — _part of day_ is not a slot, the lock button and its coral outline are
deleted, the slots are tags, _Sun 9_ is a date this app does not have, _60 min_ is a duration nothing
holds, and _COMPETITIVE_ is a search's mode rather than a game's kind — as is **press and hold for
the full record**, and as are the **pairing forecast and the player rows**, upheld with an argument
of their own: a forecast helps you decide whether to play somebody, and on this screen you already
have. The reversal is filed as [#346](https://github.com/Raketa02/Raketa/issues/346) rather than
taken.

**The plan lead is redrawn — an eyebrow and no title, three slots over two doors, nothing
pinned** ([#414](https://github.com/Raketa02/Raketa/issues/414), #410's design). `GameScreen`'s one
slot became three — `card`, `court`, `plan`, all opaque, drawn in that order on the plan lead and
nowhere else — and the screen still holds no plan, no ladder and no rung. **The eyebrow is
`formatEyebrow`'s**: the format read off the seats (the rule the Now card's retired eyebrow used,
living here now) and the kind off the game — `Doubles · Counted`, `Singles · Friendly`, stored as
words and drawn uppercase, **`Counted` and never `Competitive`** (§5.4 #8 stands), the kind clause
dropped where the build cannot read one. There is **no title under it**, the first screen in this
app without one (10.3 as amended, Part 16): the card names the people and the plan names the day,
so `gameEyebrow`'s handles and _arranged n ago_ — kept on every other arm — would be the same facts
twice. **The standing line, the shape line and the checklist go on this lead**: the card's bars say
what is agreed, the counter says how much, and the court is drawn rather than described; the
sentence about what a score records is drawn only once the grid is open, with the grid it is about.
**The two doors are in the scroll**: `Open the chat` is the app's first `dark` button, `lg` and full
width — _a filled action with no meaning attached_, which is what a wide door needs to be on a
screen that asks for nothing and so wears no accent — through the same soft-failing `useChatDoor`
join ADR-0149 §3 settles, drawn by the screen itself — which widens the seam the ADR named by one
importer, `games` reaching `conversations` for the word, the route and the join, and says so — in
a child of its own so the join is read where the door is drawn, over the one list the composition
already reads for the card's faces; and `We played` is `secondary` beneath it, opening the grid over the plan as before.
**Nothing is pinned while the grid is closed** — the design pins nothing — and the moment `We
played` opens it the footer is back with the send and `Leave it as it is`; the footer's own `We
played` went with that, because no entry arm reaches the footer with the grid closed any more (on
the score lead the grid is the screen). The score lead and the result arms keep today's screen
whole, and `result.test.tsx` asserts the entry window's sentence where it is still said.
