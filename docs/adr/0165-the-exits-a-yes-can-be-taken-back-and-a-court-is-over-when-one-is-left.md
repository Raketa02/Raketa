# ADR-0165 — The exits: a yes can be taken back, and a court is over when one is left

- **Status:** Accepted
- **Date:** 2026-09-13
- **Supersedes, by named sentence:**
  [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) §1's *"a court that
  has been a game — `ON`, or reopened since and not yet re-seated … leaving a half-built court is
  a decline, and it is already given"* — it is not given on an answered seat, and the departure
  is admitted before the court is whole (§1); §1's *"a challenge folds `game_opened` off [`SeatLeft`]"* — it folds it off the
  line-up having completed (§2); §1's and §9's *"the last person may leave too — a court everybody
  has left is a game nobody is in, and it lapses into Never played"* — the departure that leaves
  one person on a game **calls it off** (§3), and §9's *"a rule about a count that #417 replaces
  with an act"* is now a rule about a count beside the act.
  [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md) §2's
  *"in `LINE_UP_INCOMPLETE` and nowhere else"* and *"the Phase 1 withdraw is refused"* — the
  withdraw is admitted exactly while nobody besides the organiser holds an accepted seat, before
  any answer included, and refused once anybody has joined (§4); §2's argument for the refusal is
  kept as a **named, accepted risk** with its falsifier.
  [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md) §1's *"the organiser, or once the
  organiser has left, anybody still on the court"* — anybody on the court (§5).
  [#411](https://github.com/Raketa02/Raketa/issues/411)'s rule 4 (*whose act*) and rule 9 (*"a
  two does not end itself"*) — a two whose opponent leaves is over.
- **Amends** [`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §2.5's *"the row stays
  for the reader whose day ran out, and leaves at once for the reader who said no"* — and for the
  reader who **left**; and §2.5's control table, where *Withdraw* gives way to *Leave the game* and *Call it
  off* loses its fallback clause, §2.6, where the withdraw is *Remove the challenge*, and §2.1's
  arms. **Supersedes** [ADR-0150](0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
  §1's *"only the organiser may end it"* — nobody ends a court somebody else has joined; before
  anybody has, the organiser removes it.
- **Leaves standing** ADR-0162 §2 (a court that has been a game does not end by its seats), §3
  (the same game is re-seated), §4 (the moment guard), §5–§8; ADR-0163 §2–§7, including §6's
  stepping over a ghost; ADR-0142 §1 (the pair rule), §3 (the exemption's test), §4, §5; and
  [ADR-0150](0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md) §4 —
  the departed are already out of the fill's pool, and a departure before the court is whole
  lands in the same set.
- **Cites** ADR-0142 §3 for why an automatic call-off is not a second place for a derived fact
  (§3), and [#231](https://github.com/Raketa02/Raketa/issues/231) §3 for the gesture (§6).
- Settles the second half of [#420](https://github.com/Raketa02/Raketa/issues/420); built by
  [#424](https://github.com/Raketa02/Raketa/issues/424),
  [#426](https://github.com/Raketa02/Raketa/issues/426),
  [#427](https://github.com/Raketa02/Raketa/issues/427) and
  [#428](https://github.com/Raketa02/Raketa/issues/428). Grilled 2026-09-13.

## Context

**Three rules surprise the people in a room, and each is somebody else's decision doing its job.**

- **Once you have said yes to a half-built doubles you cannot get out.** `decline` refuses an
  answered seat; `leave` refuses a court that was never a game — ADR-0162 §1 wrote *"leaving a
  half-built court is a decline, and it is already given"*, which is true before you answer and
  false after — and the aggregate's own docstring hardened it to *a court that has been a game,
  and nothing else*. You wait for the court to fill, or for the organiser to withdraw.
- **Only the organiser can end anything, and not always.** ADR-0142 §2 gave the organiser the
  withdraw in `LINE_UP_INCOMPLETE` and nowhere else, destroying the room for everybody in it, and
  refused it before any answer so that a withdraw-and-resend could not hand the same person a
  fresh clock. ADR-0163 §1 gave the call-off to the organiser first and to the others only once
  the organiser had gone.
- **The fold treats the organiser as special.** A challenge that was never a game ends when *no
  seat besides the organiser's is live* — so the organiser alone is *over*, but any other player
  alone is `LINE_UP_INCOMPLETE` for good.

### The fact that decides the shape

**Nobody is in the chat separately from being on the court.** Membership is derived, never
stored (ADR-0146 §7): the challenge's accepted seats, then the game's line-up. There is no fact
to remove somebody from a room without removing them from the court, and inventing one would
leave a player counted *3 of 4 in* on a plan they no longer read. So *leave the chat* can only
mean *leave the game* — which is also what the author meant by it: *if you are not interested in
the plan any more*.

### The author's rules

Stated on the WhatsApp model, and chosen over the existing ones for **simplicity — no rule that
surprises players when the app is released**:

1. Everybody in a chat can leave it, from the list, by the same gesture; the others keep the
   chat and can fill the seat.
2. A chat exists as long as it has people in it; when everybody has left, the challenge is gone
   by itself.
3. The organiser has no power over a court somebody else has joined — but a challenge nobody has
   joined yet is the organiser's to remove, from the list or from the challenge screen.
4. Somebody who left, declined or lapsed is not proposed again for that court by the automatic
   search — which [ADR-0150](0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
   §4 already guarantees, and this record asserts rather than builds.

Rule 2 as stated — *when everybody has left* — has one hole that the fold's existing special case
was covering: a challenge nobody ever accepted, whose three invitees declined, leaves the organiser
*in* it, and under a literal reading it would never end and never leave their list, where today it
ends as *Everyone said no*. The rule that covers both is organiser-blind and is §3.

## Decision

### 1. A yes can be taken back before the court is whole

**`POST /challenges/{id}/departure` is admitted on a court that has not been a game.** The
aggregate's `not_a_game_yet` refusal goes; *an accepted seat, and nobody else's* stays; the three
endings still refuse it. The seat's answer becomes `LEFT`, the seat is open, the room is told by
the line it already has — *"{name} left — that seat is open again"* — the leaver is in the
challenge's *already asked* set and out of the fill's pool, and the pair releases on the instant.
The moment guard (ADR-0162 §4) is asked exactly where it is today: on a court that has been a
game. A half-built court has no moment to guard.

### 2. *Has this court become a game* is folded off completion

ADR-0162 §1 folded `game_opened` off `SeatLeft`, on the argument that a departure could only have
been written on a court that was `ON`. §1 makes that false. **The fold marks the court a game at
the acceptance that completes its line-up** — the instant `hand_over` opens the game — and at the
mint for a mutual-born singles, and nothing else moves it. `SeatLeft` says somebody left, and what
the fold learns from that is only what it says.

### 3. A court is over when at most one player is on it and no seat is awaiting an answer

**One rule, organiser-blind, replacing the *no live seat besides the organiser's* clause.** A
court with two or more people on it is a court; a court with one, once nobody is still deciding,
is not.

- **Before a game**, the fold reaches the two endings it has: a *no* outranks silence as today,
  and **a departure is a no** — somebody made a judgement about this court. The organiser alone
  after three declines is `DECLINED`, as today; the organiser alone after B accepted and left is
  `DECLINED` — a case that did not exist, since B could not leave; B alone after the organiser
  left is `DECLINED` too, where today the organiser could not leave either. The organiser alone
  with a seat still deciding is still arranging — and may remove it (§4).
- **On a game**, ADR-0162 §2 stands: the fold does not end a court that has been a game by its
  seats. The departure use case asks the rule after recording the departure and, when it fires,
  hands **`call_off`** to `games` on the port it already vacates the seat through, in the same
  transaction; the game is `CALLED_OFF`, the room is destroyed as for any call-off, and
  `called_by` is the player whose departure emptied the court. **Singles: an opponent who leaves
  calls the game off.** Doubles fill down to two on the court; the departure that leaves one is the one that ends it,
  however many fills came between.
- **It is not a second place for a derived fact.** ADR-0142 §3's test is *an event may announce a
  conclusion only when no arrangement of the seats could reach it*, and the seats here are the
  **game's** line-up, which cannot tell an open seat from one that is asked: a game with one
  player seated and a fill pending is not over, and only the challenge knows the difference. The
  challenge's fold reaches the reading; the game's record cannot; `GameCalledOff` is the only
  place the game's end is true, exactly as ADR-0163 §2 argued for the act.
- **A court past its entry window is untouched**: the moment guard already refuses a departure on
  a ghost, and ADR-0163 §6's leniency for a withdraw on one stands.

### 4. *Remove the challenge* — the withdraw, while nobody has joined

**The withdraw is admitted exactly while nobody besides the organiser holds an accepted seat**,
whatever seats are still awaiting an answer — and **refused once anybody has joined**. From then
on the organiser leaves like anybody else and the court ends by §3. What stays: organiser only,
whole-challenge, irreversible, the one announced conclusion, the room destroyed in the act (there
is none in the pre-answer case, and there may be one in the organiser-alone-again case). The
invitees' cards read `WITHDRAWN`, in `the-words.md` §13's sixth row as it stands.

**ADR-0142 §2's argument for refusing the pre-answer withdraw was correct and is overruled, not
refuted.** Withdraw-and-resend does hand the same person a fresh clock, and `NobodyIsAskedTwice`
still cannot see across two challenges. The author chose the organiser's exit over the
protection, on the simplicity rule, and the risk is **accepted with its falsifier named**: *the
rate of same-organiser → same-invitee resends within 24 h of a removal*. If it reads as pestering,
a cross-challenge cool-down is the follow-up — a new rule with a number to defend, which is why it
is not written now.

### 5. *Call it off* is any player's

ADR-0163 §1's rule — *the caller is still live on the court, and is the organiser or the organiser
is not* — loses its second clause: **the caller is on the court.** One code, the same sentence.
Everything else in ADR-0163 stands: the hand-over, `CALLED_OFF` as the fourth end, the wire, the
room, stepping over a ghost. A group that has given up on a game ends it in one act rather than
three departures, and that is the one place a single act beats leaving one by one — which is why
§3 does not make it redundant.

### 6. The gesture — a swipe reveals, a sheet acts

**Swipe-left on a row reveals one button; the act is behind a confirmation that names the
consequence.** Built on React Native's `PanResponder`, as the radius slider already drags, with
neither `react-native-gesture-handler` nor `reanimated` added. #231 §3's argument — the cheapest
gesture in the app must not carry the most durable act — is kept, because the swipe carries
nothing: it reveals.

| Row | Reveals | The sheet says |
| --- | --- | --- |
| a conversation | **Leave the game** | *Your seat opens for someone else and you'll leave the chat.* |
| the organiser's challenge, while nobody has joined | **Remove the challenge** | that it is gone for the invitees too |
| any other row | nothing | — |

The same acts are on the screens: the challenge screen's arranging arm gains *Leave the game*
before the court is whole; its nobody-joined arm gains *Remove the challenge* for the organiser;
*Withdraw* leaves the filling arm; *Call it off* is drawn for anybody on the court of a game with a
seat open; the game screen's *Leave this game* stays. A refusal — the moment has passed, the court
has ended — is told in words on the sheet, as the game screen tells it. **The leaver's rows go at
once**: the conversation row by membership, the challenge row by the inbox rule that already drops
an own *no* — an own *left* is the reader's own act in the same sense.

### 7. Records and copies

ADR-0142's, ADR-0162's and ADR-0163's status lines name what moved. `the-loop-screens.md` §2.5's
table and §2.6 say who holds which act. `the-words.md`'s new sentences — the sheet lines, the
call-off told by a departure, the count of who is in — are the client tickets'. The root
`CONTEXT.md`'s **Seat**, **Departure** and **Withdraw** entries say so. `backend/CLAUDE.md` still
says *only the organiser may withdraw* and describes the departure as a game's; it documents what
is **built**, so it moves with the code in #424 and #426 rather than here.

## Consequences

- **Three endings by count, order-independent.** The fold gains one rule and loses one special
  case, and the same three people with the same open seat read the same standing whichever order
  the answers came in.
- **The re-ask vector is real and accepted.** An organiser can send, remove, and send again to
  somebody who has not answered, and each send is a fresh card and a fresh clock for that person.
  The falsifier in §4 is how we will know, and the cool-down is what we will do.
- **Singles lose fill-after-departure.** #411 gave a two whose opponent left the same fill any
  court gets; §3 ends it instead. One rule for every court was chosen over two, and a singles
  whose opponent leaves is honestly a game that will not happen with that pairing.
- **The organiser loses the whole-challenge withdraw once anybody has joined.** A group that wants
  to end a half-built court that was never a game does it by leaving one by one, and the one left
  alone ends it — three taps for three people, where one tap did it before. On a game, §5's
  one-tap act is there; before one, the author took the symmetry.
- **`called_by` on an automatic call-off names somebody who did not say *call it off*.** The
  record is honest — their departure is what ended it — but the sentence the others read must say
  *left* and not *called it off*, and that sentence is [#428](https://github.com/Raketa02/Raketa/issues/428)'s.
- **Pre-answer removal has no room to destroy and nothing to tell.** The invitees learn it from
  their challenge list, or never, if the row was gone before they looked. That is the intended
  reading of a send nobody had joined.
- **Tests that pinned the old rules move**, named rather than discovered: the departure's
  *not a game yet* refusal; the fold's *organiser alone* cases; ADR-0162 §9's *the last person may
  leave and the court ghosts*; ADR-0163 §1's *withdraw is the organiser's* fallback; ADR-0142
  §2's Phase 1 refusal; and the inbox filter's own-*left* row.
- **No new dependency**, and a swipe that only reveals is a swipe #231 did not argue against. If
  the horizontal pan fights the list's scroll in testing, the fallback is a long-press to the same
  sheet, and the ticket says to say so.
