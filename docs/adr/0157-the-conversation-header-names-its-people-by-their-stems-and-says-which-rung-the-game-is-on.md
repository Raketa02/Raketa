# ADR-0157 — The conversation header names its people by their stems, and says which rung the game is on

- **Status:** Accepted
- **Date:** 2026-09-11
- **Answers [#401](https://github.com/Raketa02/Raketa/issues/401)**, part of
  [#397](https://github.com/Raketa02/Raketa/issues/397).
- **Supersedes [ADR-0148](0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
  §6 for one surface — the conversation's header — and nothing else in it.** The row that §6 is
  written about keeps every word of it: no pill, no standing, the last line is what a pill would
  have said. What is decided here is why the header is a different case, and where the line it
  draws comes from.
- **Does not touch [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §4.** *The
  whole handle or nobody* stands for every sentence and every spoken name; the header's drawn
  title is `handleStem`, which `the-words.md` §15 permits a **box** to draw — *a seat label may
  truncate visually; a sentence may not, and a spoken name never does* — and whose conditions
  this record carries.
- **Does not touch [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md).** *A
  conversation is told, and tells nothing* is a fact about the backend context, and nothing here
  makes it ask anybody anything.

## Context

**The design for the redrawn conversation screen puts two things in the header that three records
refuse.** The title line is first names — `Kuba, Ola, Zofia` — where the header draws whole
handles; and the line under it is the sport **and the game's current state, in lower case** —
`Padel · planning` — where `ConversationHeader.tsx`'s docstring, `the-loop-screens.md` §3.1 and
ADR-0148 §6 all say the subtitle is the sport and nothing else. The author has decided the design
wins. That decision is upstream of this record; what this record decides is what the two lines
**are**, so that the refusals are superseded for the reason they can be and not merely overruled.

**The first is not the reversal it looks like.** ADR-0107 §4 is against *inventing* a familiar
form: the prototype's `split(' ')[0]` over a real name produced a word the person never gave the
platform, and the client *may never derive* one. `handleStem` produces no word at all — it takes a
prefix of the handle they chose, cut at a character they typed — and what permits a box to draw
that is `the-words.md` §15, *a seat label may truncate visually; a sentence may not, and a spoken
name never does*. `handleStem`'s docstring argues it at length, with two conditions: every
sentence, every accessible name and every toast still carries the whole handle, and a handle that
opens with a break keeps all of itself. Two Play surfaces already draw it. The header is the third,
and both conditions hold there.

**The second is a reversal, and the record has to say exactly what was refused, and by whom.**
Three things refused a state here, and they did not say the same thing.

- **ADR-0148 §6** refused a state pill on the conversation **row**, on two arguments. Reading the
  design's pill *"would make the conversation ask `challenges` and `games` what they are"* — a
  cross-context read ADR-0146 forbids. And the conversation *"does not need to ask, because it has
  already been told"*: the contexts' events are written into it as system lines, so *"the last
  entry is what a pill would have said, and a pill beside it would be the second place one fact is
  true."*
- **`the-loop-screens.md` §3.1 and `ConversationHeader.tsx`** carried that to the header, and
  named the thing being refused as the prototype's subtitle — the sport plus the **card-state
  tag**, *"where the twenty-state vocabulary leaks into the chat."*

What the design asks for now answers all three. The line is *"the same state as the card in
Now"*, and the card in Now is named by a **client-side fold** the app already does — `rungOf` over
a plan and `GET /games`' own `read_at`, and `gameCardName` over a standing — producing four rungs
and a handful of endings, folded at read time from two lists every room with a game already reads
for its pinned plan card. **Nothing asks a context anything**, which is §6's first argument met.
**The vocabulary is the ladder's, not the standing's**, which is §3.1's met: `nowPresentation.ts`
says of the tag that draws the same name that it *"is affordable here because ADR-0148 §6's
refusal was about a cross-context read and a game card reads its own standing"* — the header
reads no standing at all; it takes the card's name from the feature whose card it is.

§6's second argument is the one that needs a real answer, because the room's stream *does* already
say what has happened. **It says what happened, and a rung is not that.** Two of the four rungs are
facts about the **clock**: *Today* is true of a room in which nothing has been said since Tuesday,
and *Needs result* is true of one where nobody has spoken since the game. No system line carries
either, because no act produces them — they are a reading of the plan against `read_at`, which the
stream, as a record of acts, cannot hold.

> **One of the two examples is gone, 2026-09-14, with
> [ADR-0166](0166-the-day-row-says-today-and-no-card-does.md)**: there is no *Today* rung, so the
> header never says `· today`. The argument stands on *Needs result* alone — still a reading of the
> plan against `read_at`, still carried by no line — and the header still draws the card's name. The last line on the row is the last thing somebody
*did*; the header's line is where the game *stands*, and inside a room a player is past the door
and asking the second question. The fact is not in two places, because the stream never had it.

## Decision

**We will draw the header's title as each other member's handle stem, comma-separated, and name
the header by the handles whole.** `headerTitle` is `handleStem` over `handleLine`: the stems are
shorter inputs to the rule that was already there, which still gives way by dropping whole names at
a separator and never by cutting one. The header's accessible name is `conversationHeaderLabel` —
every handle whole, joined with a final *and*, then the sport, then the state — which is §20.4's
*the visible label truncates, the spoken one never does*, and the row's own dialect one screen on.

**We will draw the sport and the game's card name under the title, in lower case, and only where
there is a game.** The name is `features/plans`' — `useGameCardName`, the ladder over the two reads
the room already makes — and the word is `cardStateWord`, a second table beside `CARD_TAG` rather
than `toLowerCase()` at a call site, because lowering a name is a decision about words and a name
that ever holds a proper noun must be able to refuse it. What crosses from `plans` into
`conversations` is a **card name** and never a standing; `conversations` learns no rung and does
the fold nowhere. A room with no game — `game_id` is nullable, and a `LINE_UP_INCOMPLETE` room has
no game and no plan — draws the sport alone, which is the same nothing the absent *Details* door
draws from the same field. No state is invented for it, and none is drawn while the games list is
still coming or for a standing this build cannot name.

**We will not draw a state on the conversation row.** §6 stands there in full: the row is a door,
the last line is what a pill would have said, and a pill beside it would be the second place one
fact is true. The header is different because a player *inside* a room is past the door — the
question is no longer *what happened last* but *where does this stand* — and because the room
already holds the two reads the answer is folded from, where the row holds neither.

**The budget the title is dropped against is counted at `h1`.** It was counted at the rows'
`cardTitle`, six points smaller — nearly half again as many characters — so the header could be
told a line fitted that did not, and a title that is not capped at one line wrapped onto a second:
the thing dropping names to a budget exists to prevent, arriving through arithmetic.
`charactersThatFit` now takes the role the line is set in, and the header says which.

## Consequences

- **The header draws a state the room did not compute.** The word comes from `features/plans`
  through its barrel and is folded from `GET /games` and `GET /plans`, so it can never disagree with
  the Now card — and it can never be more current than those two lists are. A slot filled from the
  plan card underneath lands in the plans cache on the write's own answer and the header follows;
  a standing that changed elsewhere follows on the next read of the games list, exactly as the
  rail does.
- **ADR-0148 §6 now has an exception, and the exception is bounded by a noun.** *Card name, never
  standing.* A future surface wanting to draw `AWAITING_ANSWER` on anything a conversation owns is
  refused by §6 as it stands, and this record is not a precedent for it.
- **A stemmed title can be ambiguous where whole handles were not** — two members whose handles
  share a stem draw the same word twice. The faces beside them and the whole handles in the spoken
  name are what tell them apart, and the spoken name is the one a listener has. It is the same cost
  the seat's three-character caption already pays, at a milder rate.
- **Two records and one docstring said the opposite, and all three are corrected in this
  change** — ADR-0148 §6 by a scope note at its head, `the-loop-screens.md` §3.1 by rewriting its
  two bullets, and `ConversationHeader.tsx` by rewriting its argument. Two more are **extended**
  rather than corrected: `the-words.md` §24.4 gains the header's row, and design-system 10.3 gains
  the sub-line slot the second line is drawn in, with a Part 16 row. A refusal left standing beside
  code that contradicts it is worse than either resolution.
- **The `charactersThatFit` correction makes the header drop names sooner than it did.** It was
  wrong before in the other direction, and the direction matters: a name dropped that would have
  fitted keeps the header one line tall, where a line promised that does not fit grows it a second.
  Stems being shorter is what buys the room back.
