# ADR-0174 — The radar plots the reach, and a look is not a deal

- **Status:** Accepted — **§7's *Built with*, *Three states by width* and *Tapping*
  superseded in part 2026-09-16 by
  [ADR-0176](0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md)**, from the first
  look on two devices: the field moves on `react-native-gesture-handler` and
  `react-native-reanimated` — the decision this record said a stuttering device would reopen —
  and **the card is the selection's alone at every width**; the closest width draws faces with
  their level, a tap flies at the 3 km stop or the narrower width already held, and mocks 3, 9
  and 10 no longer bind where they draw several cards. **§8's *Clustering* superseded
  2026-09-17 by ADR-0177
  §2**: at the floor only, players too close to tell apart fold into a stack a tap opens;
  above it the blob is still the truth. §1–§6, the rest of §7 and the rest of §8 stand.
- **Date:** 2026-09-16
- **Supersedes, by named sentence:**
  - [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §9's *"The toggle
    ships; the pane says it is not built … the radar is its own spec with its own argument"* —
    this is that argument (§1–§7). Its other half stands: **`radar` the glyph does not reopen**,
    because the radar is a pane of Players and not a tab, and
    [ADR-0135](0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)'s finding is untouched.
  - ADR-0169 §4's *"the card draws neither the sentence nor the tag"* — **for the deck card it
    stands.** The record sheet reached **from the radar** draws *Wants to play you* (§4), for
    §4's own reason read on a surface without an order: on the deck *"order is the only thing
    that makes the chip's promise findable"*, and the radar has no order at all. This narrows
    ADR-0109 §2 by one more shape — the
    sentence on a person the reader is already looking at, which is exactly what ADR-0169 §8
    draws in the builder's list. The list and the badge stay refused.
  - [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §2's *"`distance_km` is
    an **integer** — the underlying area is a coarse centroid and the profile's own radius is
    whole kilometres, so a decimal would claim a precision the data does not hold and would let
    *"3 km"* sit under a 3 km radius while being excluded by it"* — **one decimal, to the drawn
    spot** (§2). The precision claimed is the spot's, which is a thing the server now holds; the
    second half's cost is accepted **by name**: a player at the very edge may print *10,3 km*
    inside a 10 km reach, because the reach is measured cell to cell and the print is measured
    spot to spot, and the two are kept different on purpose so that the deck and the radar never
    disagree about who is in.
  - `the-play-screens.md` §7's *"Try the radar"*
    reaching a pane that says it is not built, and the client glossary's **Radar** — *"not
    built … until a map has an argument of its own"*. The pane is built; the glossary entry
    travels with the client ticket.
  - The profile surface's *"`change_location` … belongs to You, which is not built"* — a route
    now, and it is not You's: it is the **cold start's** (§6).
- **Amends** ADR-0131 by
  one boundary: a **reading** is not a deal and never enters the dealt memory (§4). Amends
  ADR-0104 and
  [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)
  §3 by one row: a reading is a recorded search and a prior disclosure — the *"fourth surface
  that introduces one player to another"* §3 anticipated, with its row in the register (§1).
  Amends [ADR-0089](0089-player-profile-context-event-sourced.md) by nothing: `LocationChanged`
  exists, the candidate projection already follows it, and §6 gives it its first writer after
  the commit.
- **Leaves standing** ADR-0128
  §1–§3 — a pass is still a statement about my deck; the radar is a second place to *give* one,
  and the radar itself hides nobody for it (§4);
  ADR-0101 — the reach is the
  searcher's own radius and never a partition, and there is no city (§1);
  [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) — blocks
  inherit, as it said they would, and *a gate that cannot be evaluated excludes* holds on every
  gate the radar asks (§3); [ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md)
  — the client still compares two area codes for *In your area*; bearing and the one-decimal
  distance are **served**, never derived; ADR-0107 §3 — no activity recency, so a dormant player
  is drawn at full strength; [ADR-0134](0134-the-poster-draws-a-player-and-no-value-is-invented.md)
  — the poster is the face; ADR-0169 §5, §6 and §8 — the reset, the cool-off and the builder are
  untouched, and the cool-off holds people out of the **deck** and never off the radar;
  ADR-0165 §6
  — no gesture library; the radar's pan and pinch are read from the raw touches (§7).
- **Does not decide** venues, clustering, a location picker, blocking from the radar, or the
  radius on You (§8).
- Settles the spec issue for the Radar ([#457](https://github.com/Raketa02/Raketa/issues/457));
  built by its backend and client children. **A backend and contract change.** Grilled
  2026-09-16, three rounds, at the repo root, against sixteen mocks that are **locked**.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The radar went with the Players tab, and with it the reading, its gates, the two windows, the chip, the screen and §8's list (§1, §3–§5, §7–§8); nothing calls `drawn_spot` or `bearing_deg` any more. Two decisions here still run. §6 is how a player's area moves: `PUT /players/me/location` on every cold start and on a return after more than a day, never on a plain foreground, with the You tab's one sentence. §2's print — one decimal, never below a tenth (`shown_kilometres`) — is how a club's distance is printed (ADR-0182 §6), measured from the reader's area rather than from a drawn spot.

## Context

Ania is rated in padel and tennis and lives in Kraków. Players opens on the deck, which deals
her one person at a time, ranked, each gone once answered. The deck answers *who should I
play?* It cannot answer the question people ask before they trust an app like this one — *is
there anybody out here at all?* — because a ranked queue of ten cannot tell twelve padel
players within two kilometres from three. The Players mocks draw the answer: a **radar**, Ania
at the centre, rings in kilometres, every player who plays her sport at their distance and
bearing, a face far out, a level under it closer, a small card closest. No fit ranking, no
filtering, no order. The toggle shipped with ADR-0169 and the pane said *not built*, because
ADR-0169 §9 saw the difficulty: *a map needs a location precision this platform deliberately
does not hold*.

**What the platform holds.** A location is rounded to two decimal places **on the way in** —
about a kilometre north–south, seven hundred metres east–west at Kraków's latitude — and the
precise fix never reaches the event store. The *area code* is that cell, spelled as a string.
The deck's *2 km* is the whole-kilometre distance between two cell centres, floored, and *In
your area* is code equality. Nobody's exact place exists to be drawn.

**What the prototype did.** The mocks were screenshotted from a prototype that placed each
dot at its real distance and an angle made from a hash of who the player is — *"derived from
who they are and how far away they are"* in the author's words. It solved the privacy problem
by making the compass fiction, which also makes *who lives in Podgórze* fiction, and puts
venues, when they arrive, in a false relation to people.

**What the deck already decides.** The reach of a deal is the viewer's own search radius,
1–50 km, default 10, applied as a bounding box and then an exact circle. Ten gates run before
scoring — three of them about safety and consent, the rest judgement — then four deck-only
exclusions, the quality floor, and a rank. Every yes and every pass names the deal it came
from, and the deck remembers whom it dealt for a day.

**What nobody has built.** A location is written once, at the end of onboarding, and no route
ever moves it; the aggregate has had `change_location` since ADR-0089 and the candidate
projection follows its event, but nothing calls it. A radar that draws people where onboarding
left them draws a city as it was.

The author's constraint, restated at confirmation: **the mocks are the design.** Where a mock
and a record disagree, the record is amended, as the deck and the yes screen were.

## Decision

### 1. The radar is a reading of the reach

**A reading** is the radar's request: `POST /radar` with a sport, returning every player the
radar may draw for the viewer in that sport — the **fifth surface** of the matchmaking module,
beside the shortlist, the line-up, the deck and completing a half-built game. It is a
**recorded search** (ADR-0104): an id, its rows with their Fit and breakdown, permanently, so
that the record sheet opens from every card it drew (ADR-0159 §3's fourth row), *Why 76?* can
be asked, and an answer given on it can name its origin (§4). Its rows are ordered by drawn
distance and then by player id, so the Origin key's position means something.

> **Amended 2026-09-16 (#460).** The sheet opens from a reading's card through ADR-0159 §3's
> *second* strand — *a search of the reader's returned them* — which reads no surface, so no
> fourth row was added to the prior-disclosure register: a row over the same adapter would
> be the first row twice. The fourth *row* ADR-0159 anticipated is for a surface that is not
> a search. And the order sorts on the **printed** one-decimal distance rather than the raw
> spot measurement, so that the order is reproducible off the recorded row alone; two people
> who print the same number sit by id.

**The reach is the viewer's search radius, and there is no city.** The author asked for the
whole city Ania is in, plus its suburbs, and asked which of that and the radius was doable. A
city has no source here — no table, no borders, and a phone's geocoder names a place without
drawing its edge — and a border is a line a player three kilometres from Ania's flat can fall
across, the silent exclusion ADR-0101 refused for the matcher. *City and surroundings* is a
circle without a number; the radius is that number, chosen per player, already editable. So the
radar reaches exactly as far as the deck deals, *all of them* means everyone inside the
viewer's radius, and the slider gains a visible meaning. The population is bounded by the reach
and by nothing else: no count cap, no nearest-N.

**The reading is sport-shaped, like the deal.** The Players sport chips — drawn only for a
player rated in two or more sports — sit on the radar as they sit on the deck, and both read
the one picked sport. Marek, rated in both, is on the padel radar and on the tennis radar, as
he is dealt in both decks. This is the author's own proposal, and it dissolves three
tie-breaks a sport-less radar would need: which level goes under a face, which sport's Fit
goes on a card, and which sport a yes is in.

**Two kinds of freshness.** The client refetches a reading when the pane is opened after five
minutes, on a sport switch, and on a cold start; flipping Deck → Radar → Deck inside the window
refetches nothing. A reading is not polled.

### 2. A player is a fixed spot in their cell

**The drawn spot.** Every player is drawn at one point inside their own cell: the cell's
centre offset by a fixed amount in a fixed direction, both derived from a **stable digest** of
the player's id — never the process hash, ADR-0105 — and never leaving the cell. It is the
same for every viewer, so it cannot be averaged away, and it changes only when the cell
changes. The viewer has one too and sits at the radar's origin. *Neighbourhood-true,
building-false*: the direction to Filip's **cell** is real; where inside it he is drawn says
nothing about where inside it he lives. This is the platform's existing promise — a coarse
area, never a point — doing the protecting, rather than a smudge the radar invents.

**Served, not derived.** The server works the spots out and serves, per row, **`distance_km`
to one decimal** and **`bearing_deg`**, both measured spot to spot. The client draws what it is
served and computes no geometry beyond scaling; it still compares two area codes for *In your
area* (ADR-0021).

**One decimal, everywhere.** The author's rule: the deck and the radar print the same number
for the same person. So `distance_km` on every candidate becomes the one-decimal spot-to-spot
distance, and the deck card, the record's identity line — *In your area · 0,6 km* for somebody
in Ania's own cell — and the why-fit sentence all print it. It is still omitted rather than zero
when the distance term stood down, and the smallest printed value is *0,1 km*.

**The Fit does not move.** The engine keeps measuring **cell to cell** for the distance term
and for the radius gate; the spot inside the cell reaches no score, no gate and no artifact.
The judged pairings and the ruleset diff regenerate to the same Fits, and that is the assertion
the backend ticket carries. The named cost of keeping the two measurements different: a player
at the very edge may print *10,3 km* inside a 10 km reach.

**Position is the pair's, never the card's.** Bearing sits beside `distance_km` on the row and
not inside `player_card`, for ADR-0107's rule read the way it removed `distance_km`: it is the
one kind of field whose value depends on who is looking.

### 3. The relaxed view keeps every promise and drops every judgement

The radar applies no judgement: **no level tolerance, no quality floor, no radius beyond the
reach itself, no *already has a court with you*, no cool-off, no pass memory, no dealt memory.**
Karol, who played with Ania on Saturday; Magda, passed yesterday; Marek, matched and chatting
— all drawn. A dormant account is drawn at full strength, because there is no dormancy gate
anywhere and inventing one here would be the radar's first judgement.

It keeps the gates that are somebody else's rule about being seen, or an account that cannot
be acted on: **blocked** either way, **held** (a live safety hold), **disabled** (an account an
administrator turned off — what the deck's *inactive* gate actually reads), **gender
preference** both ways, and **rated in the sport**. The author first chose *not blocked and
rated, nothing else* and asked for it to be re-verified; what changed the answer was what the
two account gates mean. Under the relaxed-est reading a disabled account is drawn at 1,2 km
with a card whose sheet will refuse to open, a player under a safety hold sits on the radar of
the person who reported them, and *show me to women only* is shown to men. None of the three is
a level, a fit, an order or a ranking. *A gate that cannot be evaluated excludes* holds for each
of the five; the four the radar does not ask are not relaxed — ADR-0099 forbids that — they are
**not asked**, because the surface has no question for them to gate.

**Fit is computed for everyone drawn**, including pairs the deck's level gate would have
refused, and the card prints it as served — *✦ 31 fit* is an honest number on a radar that
promised no floor.

### 4. One answer, two windows — and a look is not a deal

**A yes or a *not today* given on the radar is the deck's own.** Same route, same ledgers,
same 21-day life, same cap of 20 open yeses, same 30-day pass suppression, same *Show them
again*; the answer carries the reading's id as its origin. Filip, given a *not today* from the
radar, is not dealt on Ania's deck and **stays on her radar** — the radar hides nobody for a
pass (ADR-0128 §1, read on a surface that is not the deck). A mutual behaves as on the deck:
the sheet closes, the Matched! screen when a game is born, the quiet toast when the match has no
court yet, and the chat is born.

**A reading never counts as dealt.** Ania browses the radar on Monday and does nothing;
Tuesday's deck deals Filip. The dealt memory (ADR-0131) is fed by deals and by nothing else. Only
an answer reaches the deck; a look never does — the author's own restatement.

> **Amended 2026-09-16 (#460).** A reading notes no **exposure** either. The exposure ledger
> prices who has been *offered* — the zero-exposure lift and the busy sink read it to spread
> the deck's hand — and a map is not an offer; a reading that wrote it would mark every player
> in a dense city *shown* several times a day and end the lift's meaning, which is a look
> reaching the deck's order by the back door this section closes.

**The sheet's foot.** The record sheet, reached from a radar card, gains an action bar it has
never had: *Not today* and *Let's play* — the deck's two words — in the swipe's reading order — **on the radar only**; the
sheet reached from the deck's *i* stays read-only, because the deck's own buttons are one tap
away and two places to answer at once invites a double tap. Where a standing relation exists the
bar says it instead of offering blank buttons: **matched → *You're matched* and the chat**; **a
court behind or ahead → named**; **a *not today* given earlier → the two buttons still, and a
yes lifts it**; and **somebody who said yes to the viewer → *Wants to play you* above the two
buttons**, so the chip's promise is findable on a surface that has no order to do it with
(header: ADR-0169 §4 and ADR-0109 §2, narrowed). At the cap, *Let's play* on a stranger settles
and prints the deck's own sentence; on somebody who said yes, it matches.

**After an answer, the card says so.** The radar card's last line — *Tap for the full card ›*
— reads *You said yes ›* or *Not today ›* instead; the face never changes; the sheet says it in
full. The mock never shows an answered person, and replacing one line is the smallest honest
addition to it: without it, a minute of zooming around loses track of whom you have answered.

### 5. The chip is the deck's number

*N want to play you* on the radar is **`pool.want_to_play_you` computed by the deck's own
rule** — post-gate over the deck's gates, not the radar's — and served on the reading's envelope
as it is served on the deal's, so the two chips are one number and never disagree. The named
edge: Filip, whose level is too far from Ania's for the deck ever to deal him, says yes to her;
the radar draws him (§3), his sheet says *Wants to play you* (§4), and the chip does not count
him. Hidden at zero, as on the deck.

### 6. The location moves on a cold start, silently, and You says so

**`PUT /players/me/location`** calls the aggregate's `change_location`; a fix that rounds to the
cell already stored records no event and answers as if it had. The client re-reads the phone's
position **on every cold start** and **on return from the background after more than 24
hours** — never merely on foreground, which the author refused as tracking — with the accuracy
onboarding used, and puts it. A revoked permission changes nothing and says nothing: the stored
cell stays. A trip is a trip: a cold start in Lisbon moves Ania to Lisbon for everyone, and the
next cold start at home moves her back. The deck's next hand deals around the new cell; nothing
is reset. **You** carries one static sentence — *Your area updates each time you open Raketa;
it is never finer than about a kilometre.* — because silent motion with no written trace is the
one thing that would surprise a careful player.

### 7. The screen, as the mocks draw it

The numbers below are the design; the spec (`the-radar.md`)
carries every one of them with its mock.

- **Frame.** The Deck | Radar toggle and the chip are the header; the sport chips below when
  there is a choice. The field is the app's third dark surface, full-bleed. The viewer's tile is
  34 pt, ringed in volt, labelled *you*, sitting above the middle so the footer covers nobody;
  tapping it does nothing. North is up; the field never rotates with the phone.
- **Rings** from the 1 · 2 · 5 · 10 · 20 · 50 km series, drawn when their on-screen radius is
  at least 26 pt and at most about 3.5 × the screen width, labelled at the top of the circle,
  centred on the viewer and moving with them.
- **Width and ladder.** The view is named by its width in kilometres. Stops: **1,5 · 3 · 5,4 ·
  10 · 18 · 30 · 55 · 110**. The widest allowed stop is the first at or above 2.2 × the reach;
  the opening stop is the first at or above 1.8 × the reach — 30 and 18 at the default radius;
  1,5 is the floor at every radius. **±** steps to the next stop and greys at the ends; a pinch
  is continuous between the same bounds and the next ± snaps from wherever it left off.
- **Three states by width.** Above 10 km across, a 24 pt face; at 10 and below, a 30 pt face
  with the level under it; at 5,4 and below, the card. Thresholds carry a small dead-band so a
  pinch resting on one does not flicker.
- **Tapping.** A face: fly to them, centre, land at the 3 km stop, select. A card: the record
  sheet. Empty field: deselect, keep the zoom. ◉: home, opening width, deselected. A selected
  player keeps their card when the view zooms back out, above every face; nearer players are
  drawn above farther ones, the selected above all. A sport switch clears the selection and
  keeps the view; a selected player who is not in the next reading is deselected silently.
- **The card.** Face or poster, name, one-decimal distance; a rule; one sport row per sport
  the player is rated in — dot, name, level — not only the ones the viewer shares; the Fit chip
  and the reliability chip side by side, labelled, *—* when unwatched; *N tags in common* in
  mint, muted at none; *Tap for the full card ›*, or the answer line (§4). The on-court mark
  where the deck would draw it.
- **Footer.** *N players in view* counts points inside the map field between the header and
  the footer; beside it *+N off screen* or *all of them*. The hint opens with the privacy line
  at every width — *Distance and bearing only — never an address, never a street.* — then says
  how to move while faces are drawn, and that a card leads to the profile and the two answers
  once cards are. Empty reach: *Nobody within 10 km plays padel yet* and the deck's own *Your
  search radius lives in You* sentence. Loading: the tile and rings at once, *Looking around…*.
  Failure: said, with a retry.
- **Motion.** Drag with no inertia; the pinch zooms around the fingers; ± and fly-to around
  the centre; fly-to about 400 ms, instant under reduced motion. No haptic. Pan rubber-bands when
  the reach's edge reaches the screen's centre. The view is kept while the app lives — across
  tabs and across the toggle — and a cold start opens at home.
- **Built with** raw touches and the native driver, SVG for the rings; no gesture or
  animation library. If a device shows stutter, that is its own decision.
- **Accessibility.** Every face carries a spoken label — name, distance, sport and level; the
  footer's count and hint are read; the sheet is the accessible path to acting.

### 8. What it does not decide

**Venues.** The mocks draw them; nothing here serves or draws one. **Clustering.** Six hundred
faces at 18 km across is a blob, and the author chose the blob as the truth for this work; a
stack that splits as you zoom is the follow-up if a city fills up, and it is not ranking. **A
location picker.** A location is the phone's or nothing. **Blocking from the radar.** The block
route exists and no client calls it; when one does, `RADAR` is its fifth surface. **The radius
on You.** The slider lives in Find a game today and the deck's sentence already promises You;
neither moves here. **A player rated in no sport** sees on the radar what the deck shows them.

### 9. Records and copies

ADR-0169 §4 and §9, ADR-0107 §2, ADR-0109 §2, ADR-0128 §1 and ADR-0131 carry a scope note
pointing here. The root glossary gains **Radar**, **Reach**, **Reading**, **Drawn spot** and
**Bearing**, and its **Location area**, **Search radius**, **Surface**, **Pass**, **Want to play
you** and **An interest inbox** entries are rewritten in place. `the-radar.md`
is the spec; `the-play-screens.md` §7 and §12 and the specs' README point to it. The client
glossary's **Radar**, the design system's Part 16 rows, the theme and the play, shell, player
record and player profile feature records travel with the client tickets; the OpenAPI documents,
the ruleset diff, the judged pairings and the backend module records with the backend tickets.

## Consequences

- **The deck is believable.** The radar shows the population the deck ranks, with the deck's
  reach and none of its judgement; a player can see twelve faces within two kilometres before
  trusting a queue of ten.
- **The privacy promise is now literal.** *Never an address, never a street* was a copy line;
  it is now a property of what the server holds and what it serves. The cost is that *who lives
  in Podgórze* is true only to the cell, and the author accepted it.
- **`distance_km` changes type on the contract**, integer to one-decimal number, on every
  surface that carries a candidate; the client's generated types follow and three sentences
  reprint. The judged pairings and the ruleset diff must regenerate to the same Fits — the
  backend ticket asserts it, and a diff there is a defect, not a design change.
- **A reading is recorded in full, and readings are frequent.** Every open after five minutes
  writes a search with every drawn row's breakdown, for a population that is the whole reach
  and not ten. The freshness window and the reach bound it; the search record's growth is the
  price of *Why 76?* on a radar card and of the sheet opening from it.
- **The gate list forks by surface.** Five gates asked, four not asked, and the deck's chip
  computed by the deck's rule on the radar's envelope — three things a reader must hold together
  to see why the two surfaces agree. They are stated once, in §3 and §5.
- **Locations move.** For the first time since onboarding, a player's cell can change, on a
  cold start, silently. Every read of *In your area*, every deck pool and every radar follows
  the projection, as ADR-0089 built it to; the seed and the fixtures gain a second location
  event to reason about.
- **The record sheet has a foot now**, and one surface fills it. The deck's *i* does not, by
  decision, and the next surface that wants buttons on the sheet has to argue for them.
- **A third dark surface.** The design system's *paper, not glass* has one more fenced
  exception, argued here for a field that is a map of the night rather than a screen.
- **What was not built** is named in §8, so the next mock that draws a venue or a stack reopens
  a listed question rather than a settled one.
