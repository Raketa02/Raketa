# ADR-0169 — The deck lives on Players, and a swipe is an answer

- **Status:** Accepted — **§9's Radar decided and §4's *unmarked liker* narrowed for one sheet
  2026-09-16 by [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md).** **§5's reset given its storage by the amendment of 2026-09-15**
  ([#440](https://github.com/Raketa02/Raketa/issues/440)): a durable, event-free row per
  press, the fifth of the matchmaking module's ledgers.
- **Date:** 2026-09-14
- **Supersedes, by named sentence:**
  - [#231](https://github.com/Raketa02/Raketa/issues/231) §3's *"Decided: buttons only"* and its
    argument — *a swipe would be the cheapest gesture in the application attached to the most
    durable consequence in the feature* — which
    [ADR-0165](0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md) §6
    kept for the chat row and keeps there: the row's swipe still reveals. On the deck the
    consequence is no longer the most durable one (§5), and the swipe acts (§3).
  - [ADR-0109](0109-a-read-back-names-what-it-withholds.md) §2's *"Incoming-and-not-mutual never
    crosses, on any route, in any shape — not as a list, not as a count, not as a badge"* — by
    **one count, on one envelope** (§4). The list and the badge stay refused; the schema test that
    enforces the sentence is narrowed to enforce the rest of it.
  - [ADR-0128](0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)'s Context sentence
    *"there is no Show them again — that button was struck for making the suppression a
    suggestion"* and §4's *"`PASS_SUPPRESS` crosses in no shape at all"* — a route now clears it
    (§5). §1–§3 stand in full: deck only, one-directional, never escalating.
  - [ADR-0094](0094-play-intent-declared-per-sport-in-its-own-aggregate.md)'s Amendment — *"it
    reads the declaration and is refused with `play_intent_not_declared` exactly as a search is"*
    — the deck reads no declaration (§2). `DECK` stays in the closed five, stored on the events
    that carry it and never emitted again.
  - [`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §6's *"`NO_PREFERENCE →
    fun`"* mapping on the deck — now *everyone → fun* (§2) — and its *"Match me is reached from
    the screen the week is edited on"*: it is reached from a tab of its own, and the deal runs on
    the profile's week.
  - [`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §9.11's first band,
    *"People who have already said yes to you — an instant match is one tap away"*, and
    [`the-words.md`](../specs/matchmaking/the-words.md) §10's sentence *They already said yes to
    you* **on the deck card** — the liker is unmarked and placed by the nudge (§4). The sentence
    and the tag stay on the list (§8).
  - [`the-play-screens.md`](../specs/matchmaking/the-play-screens.md) §7's two-button deck, its
    *"there is still no Show them again"*, and its empty-state copy; and
    [`the-words.md`](../specs/matchmaking/the-words.md) §20.5's *two named buttons* — three
    buttons and a drag (§3), with §20.5's other half kept whole: the drag is **never the only
    path**.
  - [ADR-0135](0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)'s *"`map-pin` for
    Around"* — the tab is **Players** and draws Feather's `users` (§1). The family finding stands;
    `radar` is still not drawn, because Radar is a pane and not a tab.
- **Amends** [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §1's *"Whether a pair with an unplayed game may arrange a second one is not decided here"* — for
  the **deck only** it is decided (§6); the shortlist keeps §1's release.
  Amends [ADR-0127](0127-a-signal-expires-or-is-refused-never-quietly-decays.md) §6 by one field:
  `ttl_days` crosses beside `cap`, so a sentence may print the number without the client holding
  it (§5). The three numbers are unchanged.
  Amends [ADR-0012](0012-player-app-design-system.md) 15.4 and
  [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §2's *"the
  next dark screen argues for its own record, here"* — this is that record, for a **surface**
  and not a screen (§7).
- **Leaves standing** [ADR-0125](0125-a-full-inbox-sinks-a-player-never-withholds-them.md) — the
  lift is still `+14` and the sink still sits under it;
  [ADR-0126](0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md) — the
  deck's order still moves on facts about the player, one band fewer;
  [ADR-0131](0131-a-deal-remembers-for-a-day-so-a-spent-deal-deals-again.md) — a deal still
  remembers for a day, and §5 names the one act that forgets;
  [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §3 — no activity recency:
  the card's *around this week* is the liveness code's own existing words, drawn only when the
  code is present; [ADR-0138](0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)
  — only *allowed* draws the mark, and §7 changes its drawing, not its rule;
  [ADR-0134](0134-the-poster-draws-a-player-and-no-value-is-invented.md) — the poster is the face
  when there is no photograph; [ADR-0154](0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md)
  and [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §1 —
  the yes screen is unchanged, and *Later* pops to the deck where it now lives;
  [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §4 — the doubles line
  in §8 is one more code; [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)
  — a deal is a search, so the record sheet opens from every card.
- **Does not decide** the Radar (§9), the other side of a mutual seeing the moment (ADR-0167 §5
  stands), or the intro line, which is
  [ADR-0170](0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)'s.
- Settles the spec issue for the Players deck ([#438](https://github.com/Raketa02/Raketa/issues/438));
  built by its backend and client children. **A backend and contract change.** Grilled
  2026-09-14.

## Context

**Match me is a second screen inside Play, and it looks like a form.**

Ania — padel and tennis, Kraków — taps ⚡Play and lands on *Find a game*; a segment offers *Match
me* beside it. There she gets sport chips, a line saying which declaration the deal runs on, a
paper card with a portrait, a level row, a balance row, an overlap row, a distance line, reason
lines, and two buttons: *Not today* and *🎾 Let's play*. Holding the card explains the Fit. When
the deal is spent the card is replaced by a note. Each answer toasts. It is correct, and it is
the least inviting screen in the app for the one act the app most wants repeated.

Nine mocks arrived for it — held by the author outside the repo, at
`game_card_and_details/players/` — and they are the priority: **where a mock disagrees with the
locked design system or an accepted record, the mock wins and the record is amended.** The mocks
show a **Players** tab whose whole surface is a stack of full-bleed cards, one person each: the
level and sport top-left over the photo, a *✓ on court* mark top-right, a dark wash rising from
the bottom under the name, a meta line, a Fit badge, a quoted line, tags of which the shared ones
are volt and say *· you too*, four stat tiles (*Balance*, *Reliability*, *Overlap*, *Shared
tags*), a hint line, and a counter pill — *8 left · 12 yeses to give*. Two cards show behind the
live one. Dragging stamps the card *LET'S PLAY* or *NOT TODAY*, full at 95 px, where release
commits. Below: ✕, i, 🎾. Above: a *Deck | Radar* toggle and, when anybody is waiting, a volt chip
— *2 want to play you*. The end is *You have seen everybody*, with *Show them again* and *Try the
radar*.

**The mocks reverse five decisions this repository holds, and each was taken on purpose:**

1. **The swipe.** #231 §3 refused it — not on cost, since the radius slider already drags on the
   built-in responder, but because *Show them again* had been struck, which left a pass as a
   thirty-day act with nothing that reverses one, and a swipe would have put the cheapest gesture
   on the most durable act. `deck.test.tsx` pins the absence of a gesture library.
2. **The count.** ADR-0109 §2: a one-sided yes is silent and reaches its recipient only as a lift
   in a search *they* chose to run. *"What is gone is any version of '2 people are waiting for
   you'"*. The interest ledger has no read for *who said yes to me*, and a schema test forbids the
   count on every response type.
3. **Show them again.** ADR-0128: struck, because a button that clears every pass at once makes
   `PASS_SUPPRESS` unmeasurable and the suppression a suggestion. No route touches a pass after it
   is written.
4. **The number 14.** A yes lives 21 days (ADR-0127 §1), and §6 forbids the client to hold any of
   the three numbers.
5. **The dark card.** ADR-0012 15.4 — *there is no dark mode* — and ADR-0167 §2, which admitted the
   yes screen as the single exception and said *the next dark screen argues for its own record*.

And the mocks reverse two shapes: the deck was a **Play** surface (ADR-0094's Amendment, #227's
stack `[Now, Find a game, deck]`), and the tab where it now lives was **Around** — a placeholder
promising *players and courts near you*, drawn with `map-pin` after `radar` was refused for a
tab with no scan behind it (ADR-0135).

**Three things the mocks draw do not exist for any player, and one is another record's.** A
neighbourhood name — the platform keeps a coarse area code that is *deliberately not a
neighbourhood, a district or a city*, and prints the code nowhere. *Active now* — ADR-0107 §3
refused activity recency on any card. A decimal kilometre — distance is measured between coarse
areas in whole kilometres, and a decimal would be invented precision. The quoted line is a bio,
which the glossary refuses under *terms this context refuses*; the author decided to add one,
and that is ADR-0170.

**Two things the mocks say are subtly not today's rules.** The person who already said yes to
you is dealt *first* and the card says so; the mock wants them *shuffled a couple of cards in,
unmarked, so that discovering it stays a surprise*. And at the twenty-yes ceiling a yes on that
person is refused — the cap is checked before the mutual is — though it would never become an
outstanding yes at all.

**The relationship the author asked to be dug into.** *"What I don't want is both features —
swipe and build a game — to feel repetitive. The swipe must complement the build a game."* What
exists: a right swipe already lifts the swiper `+14` in the *other* person's shortlist with a
volt *Wants to play you* tag and admits them under the quality floor; the client then **pins**
every such row to the top of the served order regardless of Fit. On the swiper's own side the
yes vanishes — the person they said yes to is a stranger in their own shortlist. ⚡ is already
pure: the line-up composer orders by Fit and not by rank key, and never seats somebody who is in
the list only because of a yes. A padel mutual is half a game — the pair sit on one side, either
may *Fill the seats* from the chat — and nothing after *Matched!* says so. A mutual's game is
counted whatever either declared. Swiping is not activity: only signing in moves
`last_active_at`.

## Decision

### 1. The deck lives on Players, and Play is Find a game

**The second tab is Players.** Label *Players*, Feather `users` — `user` is You's, and the family
finding stands — path `/players`, key `players`; the rename is whole, because a half-rename is
the thing a later session trips over. Around's promise of courts dies with the placeholder;
courts get their own home when they arrive. The bar's inventory is still five, and it still
keeps no per-tab history: Players opens on the deck every time, and the held deal — dealt on the
first ask, found on every later one — is what makes that cheap.

**The tab has no title row.** The mock's header is the *Deck | Radar* toggle and the chip, and
that is the header. The toggle is in-screen state, not two routes; Radar is a pane with one muted
line until it is built (§9), and *Try the radar* from the empty state flips the toggle. The
*Spots* chip the empty-state mock draws top-right is dropped: the chip's slot is the count's (§4)
and is empty when the count is.

**Play loses its segment.** *Find a game | Match me* goes, `/play/deck` goes, the old screen goes;
Play opens on Find a game and nothing in the app links to the old route. The Play stack becomes
`[Now, Find a game]`. *Match me* survives as a word only in *Matched!*, whose fence ADR-0167 §4
drew.

**Sport chips appear only when there is a choice.** A player rated in one sport sees the mock
exactly; a player rated in two or more gets the chip row under the toggle, reading and writing
the same browsed sport Play's chips do. A player rated in none sees *Rate a sport first*, as
today.

### 2. The deck deals with the fun ruler for everyone, and intent has no weight on it

**No declaration is read, asked for, or needed.** The deck is a discovery surface — *who would I
like to play with?* — and the author's rule is that it shows people *regardless of the
competitive or for-fun intent*. `POST /deck` therefore scores every deal under `FOR_FUN`'s
vector — shared tags lead, overlap second, the wide `0.90` level window — for every viewer,
declared or not; `play_intent_not_declared` is never raised by it, the one-tap interstitial and
the standing line leave the deck, and `INHERITED_ON_THE_DECK` stops being a mapping for the
undecided and becomes the deck's ruler. The `DECK` surface code stays in the closed five for the
events that carry it.

**The intent term stands down on the deck.** Under one ruler a candidate who declared
*competitive* would otherwise lose the term's fourteen points for wanting a different evening
than the ruler assumes. On the deck `INTENT_ALIGNMENT` is stood down for every pairing and its
weight renormalises away — the mechanism a term already uses when it has nothing to read — so a
declaration moves nobody, up or down. Find a game is untouched: its mode still selects its
vector and the term still reads.

**Consequence, stated for the player:** Karol's Fit on Ania's Find-a-game list and on her deck
card are two numbers. The deck's is the social one, and the record sheet's breakdown says which
terms made it. The offline ruleset diff regenerates and the pull request argues it.

### 3. A swipe is an answer, and the buttons remain the path

**Dragging the card right is *Let's play*; left is *Not today*.** The stamps are invisible at
rest, fade in with the drag, and are full at 95 px, past which release commits; short of it the
card settles back. They are feedback, not buttons. The two cards behind are the next two people
in the hand, drawn as real cards, offset and scaled back, and only when that many remain. The
drag is built on the responder the app already drags with (`PanResponder`) and RN's own
`Animated` with the native driver — **no `react-native-gesture-handler`, no
`react-native-reanimated`**; the chat row and the radius slider prove the pattern. One light
haptic tick at the threshold, on `expo-haptics`, which ADR-0167 already added; off under
*reduce motion*, with the arrival and departure motion.

**The three buttons do the same two things and one more.** ✕ passes, 🎾 says yes, **i** opens the
player record sheet — the sheet the forecast card's faces already open — with the deck's
pairing in hand, so *why this Fit* lives behind the sheet's fit row. **Long-press opens the same
sheet**, which is what the mock's hint line says; the previous long-press (the Fit breakdown
directly) is reached one row further in. `the-words.md` §20.5's rule is kept in its other half:
VoiceOver and TalkBack consume the drag, so **the buttons are never removed and are the
accessible path**; the test that pinned *no gesture dependency* becomes the test that pins
*the buttons remain*.

**At the ceiling.** With no yeses to give, a right swipe on somebody who has not said yes to
the viewer does not fly: the card settles, and a toast says the ceiling — *You've given all 20
padel yeses; one comes back when it matches or lapses*. A right swipe on somebody who **has**
said yes flies and matches: the server's cap check now **exempts a yes that closes a mutual**,
because such a yes is never outstanding — it is answered the instant it is written and gives
the slot straight back. The client pre-empts from the count it now reads (§5) and the signal it
already receives (`inclusion_reason`), and the server stays the authority: a `409` still returns
the card.

**Toasts.** The stamp and the card leaving are the feedback. The pass toast and the one-sided
yes toast go; the mutual-naming-no-chat toast stays (ADR-0167 §1); the spoken result for
screen readers stays for every answer. Everything else about answering is as today — optimistic,
a refusal returns the card, offline holds the write.

### 4. The count of people waiting exists, and it is one number on the deal

**`pool.want_to_play_you`** — an integer on the deal envelope: the number of people whose live
yes towards the viewer in this sport **would be dealt to them** — passing every gate, not passed
on by the viewer within the pass window, not in the cool-off (§6), not already mutual. Not the
dealt-memory, because somebody dealt this morning and unanswered is still waiting. The chip
prints it — *2 want to play you* — and is **not drawn at zero**. It rides on the deal, so it is as
fresh as the hand: a yes that lands mid-deck shows on the next deal, and the client decrements
it when a yes on a card carrying `inclusion_reason` comes back mutual.

**This reverses a promise, knowingly.** Marek's yes was made under *silent unless mutual*; Ania
now learns that *somebody* wants her — not who. The author weighed it and took it: the count is
what makes swiping worth doing tonight, and it names nobody. ADR-0109 §2's *not as a list* and
*not as a badge* stand; the schema test that forbade the count on every response type is
narrowed to forbid the list and to allow exactly this field on exactly this envelope. The ledger
gains its first incoming read, bounded to the count — no method answers *who*.

**The liker is unmarked, and lands where the nudge puts them.** The deck's first band — *said yes
to you*, dealt first — **merges into the lifted band**: the person who said yes is ordered among
the lifted by rank key, where their `+14` already sits, so they tend to land early in the hand
and never in a fixed slot, and the card draws neither the sentence nor the tag. Their admission
under the quality floor is kept — a human's yes still outranks the engine's floor — and on the
deck the nudge is kept too (§8), because the deck has no label and order is the only thing that
makes the chip's promise findable within a sitting. Two bands, then: lifted and the rest; still
deterministic, still a fact about the player (ADR-0126).

> **Narrowed 2026-09-16 by [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §4 — for the deck card
> this stands; the record sheet reached *from the radar* draws *Wants to play you* above its two
> buttons, because the radar has no order to make the chip's promise findable with. The deck's
> *i* sheet draws nothing of the kind.

### 5. A pass can be cleared, and the deck says what is left

**`POST /api/v1/deck/reset` with `{sport}`, `204`.** *Show them again* clears, for that sport
only: every **pass suppression**, the **24-hour dealt memory** (ADR-0131's one exception, so that
*deal everyone again* is true and not mostly true), and the **cool-off** (§6). The durable record
of each pass stays — a re-shown card is still a re-show, which is the falsifier ADR-0128 §5
protects — only the hiding is lifted. Live outgoing yeses are not touched: the people Ania has
already said yes to are still hers to wait on. #231's objection is accepted as the cost: the
suppression window becomes a default rather than a rule, and its falsifier now needs the reset
excluded from the sample.

**Two endings, not one.** *You have seen everybody* — people in range, all passed, asked, dealt
or cooling off — draws the mock: *Nobody new in {radius} km today. Your yeses stay live for {ttl}
days, so the ones you gave are still working*, then *Show them again* and *Try the radar*. *Nobody
in range* — the radius is genuinely empty — keeps its own sentence and *widen it in You*, in the
same style, **without** the reset button, which would deal nobody. The number in the sentence is
**21**, not the mock's 14, and it is read from the wire: `GET /interest`'s rows gain `ttl_days`
beside `cap`, ADR-0127 §6's rule kept by making the number cross rather than by the client
holding it.

**"N left" is true.** The count of cards left was deliberately never shown, because a hand is
ten from a bigger pool and a counter that says *2 left* and then produces ten more lies. The
envelope gains **`pool.remaining`** — the people eligible after every deck exclusion and not in
this hand — and the counter prints *remaining + unanswered in hand*, counting down as she
answers. *"N yeses to give"* is `cap − outstanding`, both already on the wire; the client stops
dropping `cap`.

**Hands of ten, prefetched at two.** The deal stays ten cards under one `search_id`. The client
asks for the next hand when two remain, so the cards behind are real people and the join is
invisible; the cost is ADR-0131's — those ten are remembered for a day even if she leaves at card
nine — and it is the same cost any dealt, unanswered card already carries.

### 6. A deck-only cool-off of thirty days after a shared court

**Somebody you are already with is not in your deck, and stays out for thirty days after.** While
a challenge or a game between the two is live — arranging, planned, on, awaiting a result — and
for `deck_cool_off_days = 30` after it is behind them (played, called off, never played — the
same moment ADR-0168 lets a member leave its chat), the person is excluded from the viewer's
deck. A deck is for meeting people; a rematch is arranged in the chat the two already have.
`OPEN_CHALLENGE` already holds the pair while arranging; this extends the deck's own exclusion
over the game and the window after it, read through a port in the matcher's words over the same
counterparts the familiarity modifier already reads.

**Deck only.** Find a game keeps ADR-0142 §1's release: Ania can build next week's game with a
partner she already has one with, because a search is a question about the city. The number is a
ruleset constant of its own, deliberately equal to the pass window today, and *Show them again*
clears it with the passes.

### 7. The deck card is the app's second dark surface, and it is a surface

**The card is the photograph, or the poster, edge to edge, with a wash rising from the bottom.**
Not a dark mode, not a screen: the page behind it is paper, the buttons below it are the app's,
and the tab bar stands. ADR-0167 §2 said the next dark surface argues for its own record; this is
it, and the argument is the mock's — a face you decide about wants the whole card, and text over
a face wants a wash. The values arrive **for this card only**, written into `theme.ts` and the
design system's Part 16 in the same commit by the app ticket, as 15.3 demands:

| Value | What it is | Why it is not a copy of something |
| --- | --- | --- |
| the wash | one gradient, transparent to near-black, over the lower part of the card | the yes screen's ground is a glow on two colours; this is a scrim over a picture, and `photoScrim` is a flat tint |
| the stamps | two outlined words, rotated, one volt and one white, invisible at rest | no token, no role and no glossary entry existed; they are feedback and never controls |
| one ~24 pt sans role | the name on the card, heavy, one use | not the retired `display` back; 3.3's reasoning applies again and this is the word it applies to |
| the tick | a small vector check before *on court*, everywhere the mark is drawn | the font draws no `✓`; the mark's words, rule and spoken clause are unchanged (ADR-0138) |
| the pill | the counter, and the chip, in the chip's own radius | 4.2 as amended: the chip is the pill, and the counter is one |

The level uses the existing 40 pt figure, the tiles the existing dark-tile tokens, the Fit badge
the existing pill — which already turns coral at 90 and above, exactly as the mocks draw 97 coral
and 76 dark. Over a photograph the level and the mark take the text shadow the app already has
for text on media; no top wash, because the mock has none. Every measurement is taken from the
mocks, not from this text.

**What the card cannot draw, and what it draws instead.** No neighbourhood: the meta line is *In
your area · 2 km* when the two share an area, else *2 km*, whole kilometres. No *active now*:
*around this week* is drawn when, and only when, the deal's liveness reasons carry
`RECENT_ACTIVITY` — the code's existing words, ADR-0107 §3 intact. The quoted line is the intro
when one exists (ADR-0170), omitted when none. Tags: up to six, the **shared ones first** so the
volt *· you too* is never cut off, then the rest in the person's own order. Tiles: *Balance* from
the predicted-balance evidence, *Reliability* the Player Score, *Overlap* the shared-slot count,
*Shared tags* the count; a tile whose number is absent — the term stood down, the person
unwatched — prints *—* and the row stays four. Hint line as the mock. The poster when there is no
photograph, initials never (ADR-0167 §3's fence).

### 8. The deck collects people; the builder spends them

**The job split, as a rule.** Players answers *who would I like to play with?* — a yes is a
standing *I'd play you* for twenty-one days. Play answers *I want to play Thursday — who is
available and even?* — the builder composes a court. The deck feeds the builder in both
directions, by label, and by a nudge on one side only:

- **An incoming yes is a tag and a nudge, never a pin.** In the list Karol picks from, Ania —
  who said yes to him — carries *Wants to play you* and her `+14`, and sits where that puts her:
  earlier than her Fit alone, never above a genuinely better pairing. **The client's pin goes**:
  a liker at 51 is no longer forced above thirty people at 80. Her admission under the quality
  floor stays, for the human list only; ⚡ is unchanged — it already orders by Fit and never
  seats an admission. *"A yes informs; it never takes over."*
- **An outgoing yes is a tag only.** In the list Ania picks from, Karol carries *You said yes* —
  client-side, from her own outgoing list, which is already on the wire — and no nudge: her yes
  says nothing about his willingness. Both tags are drawn on both card styles, the two-word tag
  in place of the social card's sentence.
- **A pass never leaves the deck.** ADR-0128 §1 in full: Staś, passed on Thursday, is third in
  Ania's shortlist on Friday. A swipe-left is now the cheapest act in the app, which is one more
  reason it must not edit her searches.
- **A padel mutual says it is half a game.** The room a doubles mutual opens is born with one
  system line — a code, ADR-0146 §4, with the client's words *You two are a side. Fill the seats
  to find your opponents.* — singles rooms get none. The yes screen is untouched.
- **A mutual's game is counted unless either declared *for fun*.** The mint reads the two
  declarations for the sport and writes the challenge's mode as `FOR_FUN` when either says so;
  otherwise the mode stays absent and the existing derivation — *a friendly is a thing people
  choose* — makes the game counted. The deck ignores intent for discovery; the game honours an
  explicit wish.
- **An invitation a swipe produced says so.** When Karol's challenge reaches Ania and he is in
  her outgoing list for that sport, her challenge screen carries one line — *You said yes to
  Karol on Players*. Client-side; ADR-0143's refusal to tell an invitee *why the engine picked
  them* is untouched, because this is her own act.
- **No list of your yeses.** *12 yeses to give* invites *which eight?*, and the answer is no: a
  yes resurfaces where it matters — as the tag in the builder, and as *Matched!* — and a list
  would make the deck the admin screen the mock refuses to be.
- **The cap stays 20.** It is what keeps a yes worth something on the other side.

### 9. What it does not decide

**The Radar.** *Two ways of looking at the same set of people — the deck deals them one at a
time, the radar plots them on a map by distance.* The toggle ships; the pane says it is not
built. A map needs a location precision this platform deliberately does not hold (a coarse area,
never a point), so the radar is its own spec with its own argument, and `radar` the glyph
reopens with it (ADR-0135).

> **Decided 2026-09-16 by [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md).** The precision it holds is the
> one it draws: a fixed spot inside the cell, from a digest of the player. `radar` the glyph did
> not reopen — the radar is a pane, and ADR-0135's finding stands.

**The other side.** Marek learns of the match from his Chats list, as ADR-0167 §5 left it.

### 10. Records and copies

ADR-0109 §2, ADR-0128's Context and §4, ADR-0094's Amendment, ADR-0142 §1 and ADR-0135's
`map-pin` carry a scope note pointing here. `the-play-screens.md` §7, `the-engine.md` §10.3,
`matchmaking-engine.md` §9.11, `the-two-contracts.md` §6, `the-words.md` §10 and §20.5 and the
specs' README conflict table are rewritten in place — a spec states what is decided, and only a
record is immutable. The root glossary's *An interest inbox* moves from *terms this context
refuses* to a defined term with the fence §4 draws, and gains **Cool-off**; the client glossary
gains **Players**, **Radar**, **the stamps**, **want to play you** and **yeses to give**, and
loses *Play segment*, when the client ticket lands. The design system's Part 16 rows, the theme,
and the play, shell and shared feature records travel with the client ticket; the OpenAPI
documents, the ruleset diff and the backend module records with the backend ticket.

## Consequences

- **The deck is a tab, and the whole tab is the deck.** The one act the app wants repeated is
  one tap from anywhere and looks like what it is. Play is one screen shorter and one segment
  simpler.
- **Five refusals are reversed, each by name, and their falsifiers change.** `PASS_SUPPRESS`'s
  pass-rate-on-re-show now needs resets excluded; the *silent yes* promise is weakened to
  *nameless*; the swipe's cost is carried by the reset that made it safe. The next person to find
  any of these surprising starts here, not at the record that refused it.
- **The backend changes, and the contract changes.** Two envelope fields, one field on the
  interest rows, one route, one exemption in the cap, one band fewer, one term stood down on one
  surface, one exclusion, one system-line code, one mode written at the mint. The OpenAPI
  documents regenerate, the client's types with them, and the ruleset diff is argued in the pull
  request. Two tickets, the client's blocked by the backend's.
- **Two Fits for one pair.** A competitive player sees a lower Fit on the deck than in Find a
  game for the same person. Deliberate, and it will be asked about; the breakdown answers.
- **The count is a number that did not exist, and its definition is a list of exclusions.** The
  first time the chip says *1* and no liker turns up in the hand — because they were dealt this
  morning and remembered for a day — a player will call it a bug. It is the definition working.
- **The nudge and the surprise pull against each other.** The liker lands early because of the
  same `+14` that made them findable; a player who notices may learn that early cards are the
  likely ones. Accepted over a fixed slot, which teaches the same thing faster.
- **The pin's removal makes a yes quieter in the builder.** A liker at 51 is now at the 65 mark
  among thirty people, not first. The author chose *informs, never ranks* with that in view.
- **The cool-off hides people a player may want.** Ania played Karol on Saturday and will not
  see him on Players until mid-October; the chat is where he is. *Show them again* is the escape,
  and it also clears her passes, which she may not want. One button, one meaning.
- **The design system has a second exception, and it is a surface, not a screen.** A wash, two
  stamps, a 24 pt role, a tick and a pill radius, each fenced *for this card only*; the day the
  wash appears on a second card or the stamps on a row, the exception has become the rule. The
  tick changes the mark's drawing on every surface that draws it — that is the one value here
  that is *not* fenced, deliberately, because one mark has one drawing.
- **The mocks were drawn with posters throughout, in three colours.** The photo-when-there-is-one
  rule and the text shadow are the author's, on top of them; the build is checked against the
  mocks *and* that rule, by the author, since a session cannot see the screen.
- **A swipe is an act on a person, and it is now cheap.** Thirty days of hiding on a flick, with
  a reset that is one tap away. The counter pill and the pass toast's absence are what stand
  between a player and not noticing which way they flicked.
- **`the-two-contracts.md` §6's premise is gone.** The deck no longer takes the week as an ask;
  the deal runs on the profile's week, the prompt sheet has nothing to raise on Players, and the
  `KEEP_THESE_TIMES` prompt is Find a game's alone.
- **The tests that pinned the old shape move, named rather than discovered**: `deck.test.tsx`'s
  *cost no new gesture dependency*, *the segment*, *the footer*, the toast blocks and every
  `/play/deck` pathname; `theShell.test.tsx`'s Around placeholder; `poolOrder`'s pin; the schema
  test over incoming interest; the deck ordering and gate tests on the backend.

## Amendment — 2026-09-15: the reset is a moment on a durable row, and the fifth ledger

§5 decided the route and what it clears, and said nothing about what *Show them again* leaves
behind. [#440](https://github.com/Raketa02/Raketa/issues/440) built it, and the shape it settled
on is worth recording because the obvious one was wrong.

**A reset is one moment, and each of the three things it clears reads that moment its own
way.** The pass suppression is a Redis TTL, the dealt memory is the search record bounded by a
day, and the cool-off is `games`' courts bounded by thirty days — three stores, and a route that
*edited* all three would need to delete keys it cannot enumerate without a scan, could not touch
the search record at all, and could not touch the game. So the route writes **when it was
pressed**, per player and per sport, and the next deal applies that against the durable record
each exclusion already reads: a pass made before it no longer hides, the memory reaches back no
further than it, a court behind the pair before it no longer counts (`deck.py`:
`cleared_by_reset`, `dealt_memory_from`, `cooling_off`). Nothing is deleted and no cache is
touched — the Redis keys lapse on their own, and the deal subtracts what the pass record says
was cleared. A court still **ahead** is held out whatever was pressed: the reset clears the
window, never the game. *Already asked* is untouched, as §5 says.

**Durable, and the direction of failure is why.** Two of the three things it clears are read
from rows that do not fail soft, so a reset held in the cache would, on an outage, re-hide the
people a player had just asked to see — the *empty the deck* failure every soft ledger in the
module is soft in order to avoid, arrived at from the other end. And §5 accepted a cost only a
record can pay: `PASS_SUPPRESS`'s falsifier now excludes re-shows a reset caused, and which
those are — a deal after the moment, of somebody passed on before it — is computable only while
every moment is on file. So the table is **append-only** on the pass record's argument: a second
press is a second row, because a deal between two presses was shaped by the first, and the deal
reads the latest.

**Event-free, on the four ledgers' own argument, and this record makes it five.**
`the-engine.md` §12 exempts the search record, the interest, the pass and the prompt decline
from *state changes emit domain events*: small facts with no life story, and nothing subscribes
to one being written. A reset is exactly that — the deal reads the moment on its next run, and
that is the whole of what happens — and `backend/CLAUDE.md` says a new one does not inherit the
exemption but argues for it in an ADR. This is that argument. The `suppression_lapsed` flag is
**not** widened to cover a reset re-show: it says *the window lapsed*, and after a reset it has
not; the reset ledger beside the pass record is what names those, which is the sample §5 said
the falsifier has to exclude.
