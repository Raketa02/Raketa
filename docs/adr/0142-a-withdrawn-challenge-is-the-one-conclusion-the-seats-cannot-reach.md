# ADR-0142 — A withdrawn challenge is the one conclusion the seats cannot reach

- **Status:** Accepted — **§2's *where* superseded 2026-09-13 by ADR-0165 §4**: the withdraw is
  admitted exactly while nobody besides the organiser holds an accepted seat — before any answer
  included — and refused once anybody has joined. §1, §3, §4 and §5 stand; §2's whole-challenge,
  irreversible, organiser-only shape stands where the act still exists.
  **§1's *whether a pair with an unplayed game may arrange a second one is not decided here*
  decided for the deck only, 2026-09-14, by [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §6** — a thirty-day cool-off after a shared
  court; the shortlist keeps §1's release.
  **§3's *one exemption* — and the title's *the one conclusion* — narrowed 2026-09-15 by
  [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §1**: there are two. A court that has been a game ends
  with its game, and `challenges.called_off` announces *the game this court became is called
  off*, which no arrangement of the seats reaches either. §3's test stands word for word and is
  what the second passed; the guard that kept the count to one now names the pair. §4's `ENDED`
  is four.
- **Date:** 2026-09-07
- **Extends [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)**, which cites
  `challenges`' *nothing announces a conclusion the seats already imply* and applies it to a
  result. The rule stands; this records its **first and only exemption**, and the test that
  keeps it one.
- Settles [#325](https://github.com/Rakieta02/Rakieta/issues/325) on the map
  [#321](https://github.com/Rakieta02/Rakieta/issues/321).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** Challenges are gone, and with them the withdraw, the one-open-challenge-per-pair rule, `Standing.WITHDRAWN` and *answers challenges* (§1, §2, §4, §5). §3's test outlived the act it was written for: *an event may announce a conclusion only when no arrangement of the record could reach it* is what `games` holds `GameCalledOff`, `SeatVacated` and `LineUpReseated` to (ADR-0163). Read §3 for that rule and nothing else here.

## Context

**Three of the five standings never end, and two of them never end at all.** `standing.py`
derives a challenge's standing from its seats and the clock, and `ENDED` holds two values —
`DECLINED` and `LAPSED`. Everything downstream of *is this challenge still open* reads that set:
`Challenge.is_open_at`, `players_in_it_at`, and through them the **one-open-challenge-per-pair
rule** that `send_challenge` re-verifies in its own transaction, and the deck's exclusion
([#217](https://github.com/Rakieta02/Rakieta/issues/217): *that player has left the deck for good,
because you now have an open game together*).

Folding the aggregate forward proves two permanences:

- **A completed line-up blocks the pair forever.** Every seat accepted derives `ON`, `ON` is not
  in `ENDED`, so `is_open_at` stays true with no expiry. Two people who complete a line-up today
  are still an open pair a year later — unable to challenge each other **in any sport**, and
  removed from each other's deck permanently. `games_match_history.py` states the opposite as
  settled fact: *"A game is never open in this sense: the pair rule releases the moment a
  challenge ends, and it ends when the line-up completes into a game."* Nothing implements that
  sentence.
- **A half-built line-up blocks its pair forever, and nobody holds an exit.** A padel four where
  one player accepts and the rest lapse derives `LINE_UP_INCOMPLETE` and stays there for good:
  somebody other than the organiser is still live, so `_how_it_ended` is never reached. The
  acceptor cannot leave — `_answerable_seat` raises `TheSeatIsAlreadyAnswered` on an answered
  seat — and the organiser has no act at all. The conversation that opened on that acceptance
  never closes either.

**The one act that would have covered this is in the wrong phase.** The source documentation
gives the organiser *Challenge sent — wait or **withdraw**. No chat opens until they accept*, in
Phase 1, before anybody has answered. That is the one state where the pair block clears itself
within a day, nobody has been told anything, and no conversation exists. The documentation
describes a prototype; the act is real and the phase it was filed under is not.

## Decision

### 1. The pair rule asks whether two people are still *arranging*, not whether a challenge is over

`ON` means the arrangement is finished and a game exists — it does not mean the challenge is
over, and it must not be folded into `ENDED` to get the release. The pair rule reads its own
predicate: **a pair is held while the challenge is `AWAITING_ANSWERS` or `LINE_UP_INCOMPLETE`,
and released otherwise.** `ON` releases because the challenge's subject is finished; the two
ended standings release because there is nothing left.

This makes `games_match_history.py`'s sentence true for the first time. **Whether a pair with an
unplayed game may arrange a second one is not decided here** — that is a question about a
`games` fact, and `challenges` has no port onto it. It is filed separately; the answer taken
today is that nothing replaces the block.

### 2. The organiser may withdraw a challenge, in `LINE_UP_INCOMPLETE` and nowhere else

The rule is *the exit exists exactly where nothing else ends it*. `AWAITING_ANSWERS` ends itself
when the clocks run out. `ON` has become a game, and ending the challenge would not touch it.
`LINE_UP_INCOMPLETE` is the one standing that never ends, and it is the one that gets the act.

> **The departure half of that second sentence is superseded 2026-09-12 by [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md).** `ON` has
> become a game, and a player on it may now **leave** it — `POST /challenges/{id}/departure` —
> while the game awaits its entry and its agreed moment is ahead. The seat reopens on the
> challenge, the game is told in the same transaction, and the court is `LINE_UP_INCOMPLETE`
> again until the next completed line-up re-seats the same game. **The withdraw half is
> superseded the same day by [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md)**: a
> withdraw on a court that has been a game **does** touch it — the game is called off in the
> same transaction, `CALLED_OFF`, the fourth end — and *organiser only* gains its fallback: once
> the organiser's own seat is open, any player still on the court holds the exit, because the
> people who agreed did nothing wrong and one of them has to hold it. On a court that was never
> a game, everything in this section — organiser only, whole-challenge, irreversible, the Phase 1
> refusal — is untouched.

**Whole-challenge, and irreversible.** Per-seat would be the organiser removing an accepted
player, which `AnAcceptedPlayerMayNotBeRemoved` refuses and keeps refusing — *the people who
already agreed did nothing wrong*. A withdrawn challenge does not come back; re-asking the same
people is a **new** challenge, with fresh deadlines and its own `answered` set, which is what it
actually is.

> **Both halves of §2's *where* are superseded 2026-09-13 by ADR-0165 §4.** *In
> `LINE_UP_INCOMPLETE` and nowhere else* becomes *while nobody besides the organiser holds an
> accepted seat*: a court somebody has joined is nobody's to end for the others — the organiser
> leaves it like anybody else, and it is over by itself when one is left with nobody deciding
> (ADR-0165 §3). And **the Phase 1 refusal below is reversed**: the organiser may remove a
> challenge nobody has answered. The argument for refusing it was correct and is overruled, not
> refuted — the withdraw-and-resend vector is accepted as a named risk with its falsifier, and a
> cross-challenge cool-down is the follow-up if it fires.

**The Phase 1 withdraw is refused, and the reason is recorded so it stops being re-proposed.**
Before anybody answers, the seats lapse within 24 h and release the pair on their own, no
conversation exists, and no invitee has been told anything. What a withdraw would add there is
the ability to ask the same person again tomorrow, and again the day after: `NobodyIsAskedTwice`
is scoped to one aggregate and cannot see a withdraw-and-resend, so each resend hands that
person a fresh 24-hour clock. An act whose only unique power is hours of early release, bought
with an unpoliceable pestering vector, is not worth a route.

### 3. It is a sixth event, and it is the rule's one exemption

`events.py` refuses `GameOn`, `ChallengeDeclined` and `ChallengeExpired` because *a derived
standing has exactly one place to be true, and an event announcing a conclusion the fold already
reaches would become the second — and it would be the one that got believed.* The rule is
correct and stands.

**A withdrawal is the one conclusion no seat fact implies.** Every other standing is a reading of
the seats and the clock; this one is a decision a person took, and there is nothing in the seats
to fold it out of. The event is not a second place for the fact to be true — it is the **only**
place, and the fold reads it exactly as it reads an acceptance. The exemption is therefore
narrow and self-policing: *an event may announce a conclusion only when no arrangement of the
seats could reach it.* Nothing else in this context qualifies today, and any future candidate has
to pass that test in writing.

> **One did, on 2026-09-15:
> [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §1.**
> `ChallengeCalledOff` announces that the game a court became is called off — the seats can reach
> *deserted* and cannot reach that, because a court deserted by a fill's newcomer's *no* is not
> called off — so it is the fact's only home too. The test above is unchanged and was passed in
> writing; *nothing else qualifies* was true for eight days, and the test that keeps the count
> honest now asserts two named values rather than one.

`challenges.withdrawn` joins the durable name list at version 1.

### 4. `Standing.WITHDRAWN`, and `ENDED` grows to three

It cannot reuse `DECLINED` — nobody said no — and it cannot reuse `LAPSED` — nobody was silent.
`ENDED` becomes `{DECLINED, LAPSED, WITHDRAWN}`.

**The word is the documentation's, and only the state moved.** *Cancel* / *call off* belongs to
the plan (the prototype's *Call the game off*, and the `Cancelled` state ruled out of scope on
this map). *Stand down* is taken by the root [`CONTEXT.md`](../../CONTEXT.md): *a term that
cannot be evaluated stands down* is a platform-wide rule about a signal yielding nothing, and
reusing the phrase for a person ending something would break the one-word-one-idea rule in the
file that owns it. **Withdraw** appears nowhere in `docs/`, `backend/app` or
`frontend_player/src`, and it is what the act is.

### 5. A withdrawn invitation is not a lapse, and leaves the strand's denominator

`answering_for` keys invitations by `(player_id, answer_by)` and decides a lapse by
`now >= answer_by` alone, so a withdrawal that left the seats untouched would charge every
still-deciding invitee a lapse 24 hours later — silence on a challenge that had stopped existing.
**An invitation whose challenge was withdrawn before its deadline is neither answered nor lapsed
and is absent from the denominator**, exactly as the organiser's own seat is
([ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
*Answers challenges* prices silence, and this is not silence.

## Consequences

- **A backend contract change and its client are two sessions and two commits.** `Standing` is on
  the wire, so this is a change to `openapi.player.json` plus `make gen-api`
  ([ADR-0006](0006-backend-owns-api-contract.md)), and it is a **second** contract change
  distinct from the challenge detail read's — they are not one build ticket because they are not
  one argument.
- **[`the-words.md`](../specs/matchmaking/the-words.md) §13 gains a sixth row**, two sentences
  keyed by side: `You withdrew this` to the organiser, `{name} withdrew this — that court is
  closed` to everybody else. The invitee who never answered is told the same as the one who
  accepted; separating them would say who else was on the court. This is an addition to the
  challenge copy, not the rewrite that is out of scope.
- **The organiser's handle stops being a nicety.** The sentence names somebody and `SeatSchema`
  carries `side · player_id · answer · answer_by`, so
  [#328](https://github.com/Rakieta02/Rakieta/issues/328)'s handle is a hard dependency of this
  copy rather than a held additive field.
- **The conversation opened on the first acceptance now has an end.** Its lifetime is decided on
  #325 and belongs to a context that has no name yet; the record it needs is owed by
  [#332](https://github.com/Rakieta02/Rakieta/issues/332), which names it.
- **Nothing is written into the root `CONTEXT.md` yet.** Part 1 documents *implemented* bounded
  contexts, and `withdraw` is a decision, not a behaviour. The term lands with the build.
