# ADR-0177 — The pinch lets go where it is, and a stack opens on a tap

- **Status:** Accepted
- **Date:** 2026-09-17
- **Supersedes, by named sentence:**
  - [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §8's
    *"**Clustering.** Six hundred faces at 18 km across is a blob, and the author chose the blob
    as the truth for this work; a stack that splits as you zoom is the follow-up if a city fills
    up"* — a stack exists now, **at the floor only**, and it does not split as you zoom: it
    opens on a tap (§2). Above the floor the blob is still the truth, and zooming in is still
    the answer.
  - [`the-radar.md`](../specs/matchmaking/the-radar.md) §7.6's *"Panning rubber-bands"* read as
    covering the pinch — the pinch is **held** at the reach's edge and never banded (§1) — and
    §9's *"Clustering — faces fold into nothing"*. The spec is amended in place, and a §7.10 is
    added for the stack.
- **Narrows** [ADR-0176](0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md) §2's
  *"Everything the spec says about motion holds unchanged … the rubber band at the reach's
  edge"* — for the drag; the pinch is bound instead (§1). Everything else in 0176 stands: the
  UI thread, the one card, the gesture library and its root view.
- **Leaves standing** ADR-0174 §2: the **drawn spot** is untouched. A stack folds spots the
  platform already serves; it moves nobody and claims nothing finer than the cell.
- **A client change only.** Nothing on the wire changes. Grilled 2026-09-17 at the repo root,
  from the second look on the two devices.

## Context

The second look at the radar, after ADR-0176, found two things.

**The field jumped when a pinch let go.** Two fingers zoom, one lifts a few milliseconds
before the other, and the field leapt. Two mechanisms, both the field's. The pan gesture runs
**beside** the pinch — it has to, so that a two-finger gesture can end as a one-finger drag —
and it was anchored on the fingers' *position*, which is their average; the moment one of two
lifts, the average moves by half their spread, and the field followed it. And the pinch bound
its centre with the drag's **rubber band**: past the reach's edge the field gave a little, and
on release it sprang back over `settle` — a spring the author read, rightly, as the field
*adjusting somehow*. A drag past the edge is a finger asking for something the reach refuses,
and the spring is the refusal made visible; a pinch past the edge is nobody asking for
anything, and a spring there is the field moving on its own.

**At the floor, faces still lay on one another.** The floor is 1,5 km across — 260 points to
the kilometre on a 390 pt phone — and a closer face is 34 pt with its ring. Two players whose
drawn spots are nearer than that lie on one another at the narrowest view there is, and the
one underneath cannot be tapped; ADR-0176 §3's one-card rule made the card reachable and did
nothing for the face. It is not rare. The drawn spot puts each player at a stable offset inside
their cell (ADR-0174 §2), and two of nineteen in one cell land within 130 m of each other more
often than not. The author asked for the map idiom — *marker clustering*, and the *spiderfy*
that opens a cluster on a tap — **precise, and only for players who are very, very close**,
with the range to be defined.

**What the range is.** The problem is a drawing problem — two faces on one spot — so the rule
is the drawing's: two players are *too close* when their spots lie **nearer than one face is
wide** on the field, at the floor. That is 34 pt, which on a 390 pt phone is 0,131 km and on
a wider one less; it is the exact distance at which a finger cannot tell them apart and not a
metre looser. Any rule in kilometres alone would either fold faces that were already apart on a
wide phone or leave faces on one another on a narrow one. And the rule holds **at the floor
only**: above it, closer is always the answer, and a stack there would be a judgement about
who is worth a face — which ADR-0174 §3 refuses on this surface.

## Decision

### 1. The pinch lets go where it is

The drag is anchored on the recogniser's **translation** — the travel since the gesture
began, which the recogniser keeps continuous as a finger lands or lifts — and never on the
fingers' position. When a pinch ends with one finger still down, the drag is anchored afresh at
the travel last reported and the view the pinch left, so the finger that stays continues from
where the field is. And the pinch **holds** its centre inside the reach: `pinched` binds where
`dragged` bands, so a pinch that would carry the centre past the edge stops at the edge, and a
release has nothing to spring back from. Only a drag rubber-bands, as §7.6 always said.

**Amended 2026-09-17 — the pointer count, not the recogniser's end.** On Android the gesture
library's pinch does not end when one of the two fingers lifts: it stays active on the finger
that remains, with one pointer, and reports *that finger* as the focal point — half a spread
from the midpoint it reported a frame earlier. Read as a pinch, that put the kilometre under
the old midpoint under the remaining finger: the jump this section was written to remove,
still on the phone, and *random* because it is half of whatever the spread was, in whichever
direction the finger that lifted was. iOS's recogniser ends at fewer than two touches, which is
why the pan-side fix above looked complete there. **The pinch is therefore over the moment an
event carries fewer than two pointers, whatever the recogniser says**: the hand-off to the
drag happens on that event, and a one-pointer pinch event moves nothing. Two smaller things
came with it. The pinch starts from the spread the recogniser *activates at* rather than from
1 — Android activates a slop late and reports the ratio it has already reached, which measured
from 1 was a zoom of that much on the first frame. And a release compares the centre to the
edge within a hair rather than exactly: a centre the pinch held at the edge comes back through
the transform an ulp outside it, and that started a settle of nothing.

### 2. A stack at the floor, opened by a tap

At the floor, players whose spots lie nearer than one face is wide — taken across, so A over B
and B over C is one stack of three — are folded into a **stack**: one marker at the mean of
their spots, a face-sized paper square with the count in mono, spoken *N players close
together*. The members are not drawn. A stack forms at no other width.

**A tap on the marker opens it.** The members fan out around the marker on rings — the first a
touch target from it, each a face's width and a step apart, from north clockwise, a further
ring when one is full — each a face at their usual size, each with a hairline back to the
marker so a face spread from its spot still says where it came from. The marker turns volt and
says it is open. A tap on a fanned face flies to where the fan put them, at the floor, and
selects them: their card opens at the fanned spot with the fan still standing. A tap on the
marker again, a tap on empty field, or a zoom off the floor folds them back; the selection is
kept, and a selected member of a folded stack is still their card, at their own spot, above
the marker — the one card is the one card. The hint at the floor gains a sentence while a stack
stands: *A number is players too close to tell apart; tap it to spread them.*

The fan is laid out in points at the floor's scale and carried as kilometre points, so a fanned
face rides the field's transform like any tile; the legs are drawn as the rings are, on the UI
thread in the field's own points, because a hairline inside the transform is a smear.

### 3. What a stack is not

Not clustering above the floor: the blob at 18 km is still the truth, and zooming in is still
what separates it. Not a count that replaces the footer's: *N players in view* counts spots,
and a stack of three is three. Not a judgement: the members are whoever is too close, in the
served order, and the marker ranks nobody. Not a new spot: nobody moves; a fanned face is a
face drawn somewhere else for as long as the fan is open, and its distance and bearing are
what they were.

## Consequences

- **The pinch's edge is a wall now, not a band.** A pinch zooming out near the edge of the
  reach stops moving the centre when it reaches it, while the fingers go on — the point under
  the fingers stops following them for that part of the gesture. The trade is a release that
  never moves the field on its own, which is what was asked for.
- **A stack is one more state the tile layer draws**, and one more thing a test walks: the
  fold, the fan, the flight to a fanned spot, the fold-back, the dissolve off the floor. The
  open stack is the field's own state, by the stack's id, and dies with the pane like the fan
  itself; the store keeps the view and the selection and knows nothing of stacks.
- **The rule is in points, so it is per phone.** 34 pt is 0,131 km on a 390 pt field and 0,119
  on a 430; two players fold on one phone and stand apart on another. That is the rule
  working: the question is whether *this* screen can tell them apart.
- **The hand-off between two simultaneous gestures cannot be driven through the gesture
  library's jest utilities**, which end every gesture they fire. §1's anchoring is argued from
  the recogniser's contract and pinned where it can be — the hard bound, in the geometry — and
  the rest is the author's look on both devices. **Nothing here has been seen on a device.**
  *(It was, on 2026-09-17, and the hand-off failed on Android for the reason §1's amendment
  records; the suite now plays Android's one-pointer event and the slop-late activation, and
  both are red on the code as first written.)*
