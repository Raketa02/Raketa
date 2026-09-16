# The radar — who is actually out there

> **Decided by [ADR-0174](../../adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)**
> (2026-09-16), the spec issue is [#457](https://github.com/Raketa02/Raketa/issues/457), and
> the sixteen mocks in [`radar-mocks/`](radar-mocks/) are **locked**: where a mock and a record
> disagree, the record is amended. This file is what the backend serves and what the Players
> tab's second pane is owed by it, in the shape of
> [`the-play-screens.md`](the-play-screens.md); every sentence the pane says is in
> [`the-words.md`](the-words.md) §26.

**The cast**, reused throughout. **Ania** is the viewer — rated in padel (2,70) and tennis
(3,10), lives in Kraków, search radius 10 km. **Filip N.** — padel 2,60, 1,9 km. **Marek Z.**
— padel 2,92 *and* tennis 3,40, 4,8 km. **Zofia B.** — tennis only, 12 km. **Karol T.** — padel
2,75, 1,2 km; he and Ania played last Saturday. **Magda P.** — padel 2,66, 2,4 km; Ania said
*not today* to her on the deck yesterday. **Piotr** — padel, Warsaw, 250 km away.

---

## 1. The question

The deck answers *who should I play?* — ranked, dealt one at a time, gone once answered. The
radar answers *who is actually out there?* — everyone rated in the sport Ania is looking at,
within her reach, at their distance and bearing from her, with **no fit ranking, no filtering,
no order**. It exists because a queue of ten cannot tell twelve padel players within two
kilometres from three, and that is the thing people want to know before they trust the deck.
*It is the map that makes the deck believable.*

Two ways of reading the same set of people: the deck judges an order; the radar puts people
where they are. Both read the one sport picked on the Players chips. Marek is on the padel
radar and on the tennis radar, as he is dealt in both decks. Piotr is on neither: he is outside
Ania's reach.

---

## 2. The reading — `POST /radar`

**Request:** `{ sport }`, nothing else. No radius (it is the profile's), no mode (there is
none), no position (the server holds the viewer's cell).

**A reading is a recorded search** — the fifth surface, `RADAR`, beside the shortlist, the
line-up, the deck and completing a half-built game — with a `search_id`, rows kept with their
Fit and breakdown for ever (ADR-0104), a row in the prior-disclosure register so the record
sheet opens from every card it drew (ADR-0159 §3), and an Origin key an answer can name. The
rows are ordered by **drawn distance, then player id**, so a position means something.

**A reading is not a deal.** It enters no dealt memory, spends no hand, and is not counted
where deals are counted (ADR-0131, ADR-0174 §4).

**Envelope** — the deal envelope's shape, reused: `search_id`, `pool { radius_km_used,
players_in_range, want_to_play_you }`, `ruleset_version`, `engine_version`, `my_area_code`.
`players_in_range` is the reading's own row count. `want_to_play_you` is **the deck's number**,
computed by the deck's rule — post-gate over the deck's ten gates, minus passes, cool-off and
mutuals — so the chip on either pane is one number ([ADR-0174](../../adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
§5). Omitted at zero.

**Row** — a candidate, plus position:

| Field | What | Note |
| --- | --- | --- |
| `player_id` | | |
| `fit` | 0–100, as served | computed for everyone drawn, floor or no floor |
| `distance_km` | **one decimal**, spot to spot | the same field, the same number, as on every other candidate (§4) |
| `bearing_deg` | 0–359, from the viewer's spot to theirs, north 0, clockwise | **radar rows only** — the one position field the deck does not need; beside `distance_km` on the row and never inside `player_card` (ADR-0107) |
| `player_card` | the closed list, unchanged: name, `photo_url?`, `review?`, `area_code`, `social_tags[]`, `level` in the reading's sport, `band`, `range`, `intro?`, `player_score?`, `counted_games?`, `last_five?` | |
| `ratings[]` | `{ sport, level }` for **every** sport the player is rated in | the card's sport rows (§7); a fact the subject published, per sport |
| `terms[]` · `concerns[]` · `degraded_terms[]` · `modifiers[]` · `liveness_reasons[]` | as on a deal | *N tags in common* is derived from the `playing_style` / `social_vibe` evidence exactly as the deck derives it — the same function, not a served count |
| `inclusion_reason?` | `INTEREST_LIFT` when they said yes to the viewer | the sheet's *Wants to play you* line reads it (§5) |

**No pagination, no count cap.** The population is bounded by the reach and by nothing else.
A reading's cost is named in ADR-0174's Consequences and bounded by the freshness rule below.

**Freshness.** The client refetches a reading when the Radar pane is opened and the held one is
older than **five minutes**, on a sport switch, and on a cold start. Deck → Radar → Deck inside
the window refetches nothing. No polling.

---

## 3. Who is drawn

Everyone within the viewer's **reach** — their own search radius, 1–50 km, the same bounding
box then exact circle the deck uses, measured **cell to cell** — who is rated in the reading's
sport, and who passes the five gates the radar asks:

| Gate | Asked? | Why |
| --- | --- | --- |
| `BLOCKED` (either way, fails closed) | **yes** | ADR-0095: blocks inherit |
| `HELD_ACCOUNT` (a live safety hold) | **yes** | a person under a hold does not appear on the radar of the person who reported them |
| `ACCOUNT_INACTIVE` (an account an administrator disabled) | **yes** | a card whose sheet cannot open |
| `GENDER_PREFERENCE` (both ways, fails closed) | **yes** | a rule somebody set about who may see them |
| `NOT_RATED` (in this sport) | **yes** | the population is the sport's |
| `OUTSIDE_RADIUS` | *is the reach* | the circle is the population bound, not a gate on it |
| `OPEN_CHALLENGE` | **not asked** | a court with the viewer is a line on the sheet (§5), never a hole on the map |
| `LEVEL` | **not asked** | *no level band* |
| `PHOTO` · `PROPOSALS_OPT_OUT` | **not asked** | inert today; engine-initiated only |

And **none of the deck's exclusions**: no pass memory, no dealt memory, no cool-off, no
quality floor, no *already asked*. Karol (played Saturday), Magda (passed yesterday) and Marek
(matched) are drawn. A dormant account is drawn at full strength — there is no dormancy gate
anywhere, and the radar does not invent one.

*A gate that cannot be evaluated excludes* (ADR-0095) holds for each of the five; the ones not
asked are not relaxed (ADR-0099) — the surface has no question for them to gate.

**Empty** is a reading with no rows: the pane says so (§7) and offers the deck's own sentence
about widening the radius.

---

## 4. The drawn spot

Nobody's exact place exists: a location is rounded to a two-decimal cell on the way in (about
a kilometre north–south, ~700 m east–west at Kraków), and the precise fix never reaches the
event store. The radar draws each player at **one fixed spot inside their own cell**:

- the cell's centre, offset by an amount and a direction both derived from a **stable digest
  of the player id** (never the process hash — ADR-0105), never leaving the cell;
- the same for every viewer, so it cannot be averaged away;
- unchanged until the player's cell changes.

The viewer has one and sits at the origin. **`distance_km`** is the spot-to-spot distance,
rounded to one decimal, never printed below *0,1 km*, still omitted when the distance term stood
down. **`bearing_deg`** is spot to spot, north 0, clockwise.

**The same number everywhere.** `distance_km` on *every* candidate — shortlist, line-up, deck,
fill — is this one-decimal spot distance now, and the deck card, the record's identity line
(*In your area · 0,6 km* for somebody in Ania's own cell; *In your area* is still code equality)
and the why-fit sentence print it. Nothing prints a whole kilometre any more.

**The Fit does not move.** The engine's distance term and the radius gate keep measuring cell
to cell; the spot reaches no score, no gate, no artifact. The judged pairings and the ruleset
diff regenerate to the same Fits. The named cost: a player at the very edge may print *10,3 km*
inside a 10 km reach.

---

## 5. Acting on somebody

**One answer, two windows.** *Let's play* is `POST /interest`, *Not today* is `POST /passes`, both
carrying the **reading's** `search_id` and the row's position as their Origin key — the same
routes, ledgers and numbers as the deck: 21-day yes, cap of 20, 30-day pass suppression, one
*Show them again*, mutual exemption at the cap. A radar answer reaches the deck; **a look never
does**.

After an answer the person **stays on the radar** — the radar hides nobody for a pass (ADR-0128
§1 read on a surface that is not the deck) — and their card's last line says *You said yes ›*
or *Not today ›* in place of *Tap for the full card ›*. Their face never changes.

**The sheet's foot** (radar only; the sheet from the deck's *i* stays read-only):

| Standing relation | The foot shows |
| --- | --- |
| none | **Not today** · **Let's play** — the deck's two words, `secondary` and `primary`, the swipe's reading order |
| they said yes to the viewer (`inclusion_reason`) | *Wants to play you* above the two buttons; *Let's play* matches |
| the viewer said *not today* earlier | the two buttons; *Let's play* lifts the pass |
| the viewer said yes earlier | *You said yes* · *Not today* only |
| matched (mutual, live) | *You're matched* and the door to the chat |
| a live challenge or game together, or one behind them | the court, named, and no buttons |
| at the cap, a stranger | *Let's play* settles and prints the deck's cap sentence |

**A mutual** behaves exactly as on the deck: the sheet closes; the Matched! screen when a game
is born; the quiet *You both said yes* toast when the match has no court yet; the chat is born.

---

## 6. The location moves on a cold start

**`PUT /players/me/location`** `{ latitude, longitude }` → `204`. The aggregate's
`change_location`: a fix rounding to the stored cell records no event and still answers `204`.
The candidate projection already follows `LocationChanged`; every deck pool, every radar and
every *In your area* follows the projection.

**The client** re-reads the phone's position with onboarding's accuracy **on every cold
start** and **on return from the background after more than 24 hours** — never merely on
foreground — and puts it, silently. A revoked permission: nothing happens, nothing is said, the
stored cell stays. A trip is a trip. The deck's next hand deals around the new cell; nothing is
reset; the radar refetches.

**You** carries one static sentence (§26 of the words): *Your area updates each time you open
Raketa; it is never finer than about a kilometre.*

---

## 7. The screen

Sizes in points. Widths in kilometres are **the width of the map field**, so a wider phone
sees more of the same picture at the same scale.

### 7.1 Frame — mocks 1, 4

The Players header: **Deck | Radar** toggle (6.3) in the lead slot, the volt chip *N want to
play you* on the right when N > 0; the sport chips beneath only for a player rated in 2+
sports, shared with the deck. Under it the field, **full-bleed, the app's third dark surface**
(2.1 / 15.4 fenced, argued in ADR-0174 §7): the night gradient of mock 1. The footer sits on
the field's bottom edge, above the tab bar.

### 7.2 You, and the rings — mocks 5, 6

- **You**: a 34 pt square tile, your photo or poster, a volt ring, the word *you* beneath in
  `tiny`. Placed on the field's vertical **42 %** at home, so the footer covers nobody.
  Tapping it does nothing.
- **Rings**: the series 1 · 2 · 5 · 10 · 20 · 50 km. A ring is drawn when its on-screen radius
  is **≥ 26 pt and ≤ 3.5 × the field's width** — two or three at any width, never a bullseye.
  Labelled at the top of the circle in mono `tiny` (*5 km*). Centred on you and moving with you
  when you pan, because they measure distance from you and not from the screen.
- **North is up.** No compass, no rotation.

### 7.3 Width, the ladder and the three states — mocks 7, 8, 9, 15

| | |
| --- | --- |
| **Stops** | 1,5 · 3 · 5,4 · 10 · 18 · 30 · 55 · 110 km |
| **Widest** | the first stop ≥ 2.2 × reach (30 at the default 10 km) |
| **Opening** | the first stop ≥ 1.8 × reach (18 at the default) |
| **Floor** | 1,5 km, at every reach |
| **±** | to the next stop; greyed at the ends |
| **Pinch** | continuous between floor and widest, around the fingers; the next ± snaps to the next stop from wherever the pinch left off |
| **Counter** | the current width, mono, between the buttons — *18 km across* — always |

| State | Width | The player is drawn as |
| --- | --- | --- |
| **Wide** | above 10 km | a **24 pt** face — photo or poster, a 6 pt corner — and nothing else |
| **Closer** | ≤ 10 km | a **30 pt** face with their level in the reading's sport beneath, mono `tiny` (*2,66*) |
| **Closest** | ≤ 5,4 km | the **card** (7.4) |

Thresholds carry a small dead-band (about 3 %) so a pinch resting on one does not flicker.

### 7.4 The card — mocks 10–14

A paper card, ~190 pt wide, radius 13, anchored so its top-left sits at the player's spot:

1. **Identity** — a 34 pt face (photo, or the poster; the mocks' *FN* / *MP* are the poster's
   place), the name (`deckName`'s smaller sibling, `h2`), the distance in mono `tiny` (*1,9
   km*). The on-court mark where the deck would draw it.
2. **A rule** (5.3).
3. **One sport row per sport the player is rated in** — not only the sports the viewer shares:
   the sport's 6 pt dot (2.3, always with the name), the sport name as an eyebrow, the level
   right-aligned in mono (*2,60*). The reading's sport first, the rest in registry order.
4. **The two scores**, side by side, labelled: the Fit pill (7.10, `✦ 76 fit`, dark) and the
   reliability chip (`88 reliability`, paper2). *—* where the reliability is unwatched.
5. **Tags in common** — *N tags in common* in mint when N > 0, *no tags in common* muted. A
   count, never a list.
6. **The last line** — *Tap for the full card ›* in coral; or *You said yes ›* / *Not today ›*
   after an answer (§5). **The whole card is the target.**

Nearer players are drawn above farther ones; the selected above all.

### 7.5 Tapping, flying, selecting — mocks 2, 3

| Tap | Effect |
| --- | --- |
| a face (wide or closer) | the view **flies** to them (~400 ms ease; instant under reduced motion), centres on them, lands at the **3 km** stop, and they are **selected** |
| a card | the record sheet, with §5's foot; no flight |
| the field | deselect; the zoom stays |
| ◉ | home: centred on you, the opening width, deselected |
| a face while another is selected | switch selection and fly |

A selected player **keeps their card** when the view zooms back out past 5,4 km, drawn at the
face's position above every face; tapping that card opens the sheet. A sport switch clears the
selection and keeps position and zoom; a selected player absent from the next reading is
deselected silently.

### 7.6 Moving — mock 1

Drag anywhere; the field follows the finger with **no inertia** and settles where it is let
go. Panning **rubber-bands** when the reach's edge reaches the screen's centre. ± and the
fly-to zoom around the screen's centre; the pinch around the fingers. No haptic on the radar.

The view — position, zoom, selection — is **kept while the app lives**: across the Deck |
Radar toggle and across tabs. A cold start opens at home.

### 7.7 The footer — mock 16

- **Headline**: *N players in view* — a player is in view when their **point** (the spot, not
  the card) lies inside the field between the header and the footer; recounted on every move.
  Beside it, right-aligned, *+N off screen* or *all of them*, so the count is never mistaken for
  the population.
- **Hint**: always opens with the privacy line — *Distance and bearing only — never an
  address, never a street.* — then, while faces or levels are drawn, *Drag to move, pinch or use
  ± to zoom, tap anybody to fly to them.*; once cards are drawn, *Tap a card for the full
  profile and the two answers.* The hint switches on the **zoom state**, never on selection.
- **Empty reading**: headline *Nobody within {reach} km plays {sport} yet*; hint the deck's own
  *Your search radius lives in You. Widening it is what brings more people into range.* The
  field still draws you and the rings.
- **Loading**: you and the rings at once; headline *Looking around…*; the privacy line.
- **Failure**: headline *The radar couldn't load*; a *Try again* text button in the hint's
  place.

### 7.8 Accessibility

Every face and card carries a spoken label — *{name}, {distance} km, {sport} {level}* — and
acts as a button. The footer's headline and hint are read. ± and ◉ are labelled (*Zoom in*,
*Zoom out*, *Back to you*). The sheet is the accessible path to acting; nothing is answerable
from the field itself.

### 7.9 Built with

Raw touches for the pan and the two-finger pinch, the field's transform on the native driver,
`react-native-svg` for the rings, absolutely positioned tiles counter-scaled so a face is
always 24 or 30 pt. **No gesture or animation library** (ADR-0165 §6); a device that stutters
reopens that as its own decision.

---

## 8. Seams, and what a good test is

**Backend.** The reading is a use case at the application seam, like the deal: tests drive it
through the workbench with a fixture city and assert **who is drawn** (the five gates; Karol,
Magda and Marek present; the level-far pair present with a Fit), **the order**, **the envelope's
chip equalling the deal's** on the same fixture, and **that no dealt memory was written**. The
drawn spot is a pure function of `(player_id, cell)` — asserted stable, inside the cell, and
digest-based. `distance_km`'s one decimal is asserted on every surface's response and the
judged-pairings and ruleset-diff regenerations asserted **unchanged in Fit**. The location route
is asserted through the aggregate: same cell → no event; new cell → `LocationChanged` and the
projection moved. Prior art: the deck's `run_deck_deal` tests, the fence tests, the
profile-surface route tests.

**Client.** The radar's geometry — km → pt, the ladder and its bounds from the reach, the state
by width, ring selection, in-view counting, the fly-to target — is a set of pure functions
tested without rendering. The pane is tested through the router harness with a served reading:
the three states, a tap flying and selecting, the selected card surviving a zoom-out, the
footer's numbers, the chips refetching, the empty and failing readings. The sheet's foot is
tested per relation. The cold-start refresh is tested through the platform location port's fake
and the profile API mock: cold start puts; foreground under 24 h does not; revoked does nothing.
Prior art: `deck.test.tsx`, `promptSheet.test.tsx`, `useLocationStep`'s tests.

---

## 9. Out of scope

Venues (the mocks' ◎). Clustering — faces fold into nothing; the blob is the truth for this
work. A location picker. Blocking from the radar (`RADAR` is the block's fifth surface when a
client calls the route). Moving the radius slider to You. Polling or live updates. Edge arrows
for off-screen players. A dormancy fade.
