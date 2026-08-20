# ADR-0048 — Silence confirms a result, and disagreement must carry a score

- **Status:** Accepted
- **Date:** 2026-08-20
- **Reverses:** the post-play rule in `3.1` §1.4 and `now-section-domain-spec.md` §5d, which sent
  an entered-but-unconfirmed result to `playedNoScore`

## Context

The shipped rule discards a result nobody agreed to. Thirty minutes after the final point, both
*nobody entered anything* and *somebody entered it and nobody agreed* resolve to `playedNoScore`
— the match counts for nobody. Confirmation is one tap, from the opposing side only, and no
document in the set describes a counter-proposal of any kind.

**That rule pays the loser to do nothing.** Kuba enters the correct score; Marta's phone is in her
bag; the match is discarded. Kuba is punished for Marta's inaction and Marta is not punished at
all — and because she lost, ignoring the prompt is *strictly her best move*: it protects the
level that decides which matches she is offered. Levels then drift only upward, and every engine
that ranks against them is ranking against numbers that have stopped describing anybody. The
product starves on the same rule: levels, fit and matchmaking all run on **counted** matches, and
this discards exactly the ones that were played properly.

Two facts bound the redesign. **The result window is thirty minutes and we cannot reach anybody
inside it** — Raketa sends nothing to a phone
([ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md)), so the prompt exists only
for a player who has already opened the app. And **the four Player Score strands do not contain
this behaviour**: they are attendance, late cancellations, payment failures and replacement
success, published as *"what clears it: turning up — nothing else"*, and the engine's own
definition of the number is *the fraction of matches this player committed to that they actually
played*. A player who turned up, played and paid scores full marks on it, correctly.

## Decision

**Silence confirms.** A result nobody answers stands when its window closes, and the match counts.

**Every version of the result is proposed by a side, and each side may propose once.** The people
who may act are those holding paid seats when the match ended — never a leaver, never a standby
player ([ADR-0030](0030-a-departure-is-an-audience-not-a-state.md)).

- **Entering.** Any of them may enter the result. The card asks for it in the first **30 minutes**,
  while both sides are still at the club; entry is permitted for **24 hours after the match ends**.
  Nobody enters inside 24 hours → the match is uncounted.
- **Correcting.** The proposing side may revise its own proposal freely until the other side
  responds. A correction is not a second proposal — the three attempts exist to bound an argument
  between two sides, and a player fixing his own typing before anyone has read it is not one.
- **Accepting.** Only from the **opposing** side, because a teammate agreeing with a teammate
  proves nothing. **One opponent suffices.**
- **The acceptance grace.** An acceptance does not settle the result until **30 minutes after the
  proposal was entered**. Inside that window a counter-proposal beats a pending acceptance. In a
  four-player match somebody is always slower to their phone, and without this a partner's fast
  tap closes the door on an opponent who was still in the shower.
- **Countering.** Anyone who played may counter, **including a player on the proposing side** —
  the rule that makes a teammate's agreement worthless is the same rule that makes a teammate's
  objection credible. **A counter must carry a score.** There is no bare rejection.
- **Settlement.** A lone proposal unanswered for **24 hours** stands. Once **both** sides have
  proposed, only an explicit acceptance settles it; if neither side accepts the other's within
  24 hours, the match is **uncounted**.
- **Finality.** A settled result is final. There is no support correction path and no reversal.

**We will not arbitrate.** Two people who were both on court and cannot agree what happened is not
a result, and Raketa will not invent one.

## Considered options

**A bare rejection button, with the disagreement resolved in match chat** — the shape the ticket
arrived with. Rejected twice over. A rejection carrying no score is **free and always optimal for
the loser**: two minutes before the result stands, Marta taps reject, the result is suspended, her
level never moves, and she has done exactly what this ADR exists to stop, with a button provided
for it. Requiring a score makes the objection specific, falsifiable, made in front of three people
who were there, and — because the counter is itself a proposal — settled by the other side's
silence in turn, so **disengaging is never safe for anybody**. And chat does not exist: it is
promised in the product vision and written nowhere, so the flow pointed at a room that had not
been built. With the disagreement expressed in scores there is nothing to type.

**Three proposals rather than two.** The third does no work. By the time two different scores are
on the table, a third is one side repeating itself, and the extra day buys delay rather than
resolution.

**Silence confirming the *last* proposal too**, so nothing can ever be killed by disengaging. It
removes the escape hatch below and replaces it with a worse one: whoever types last wins, which
players find in a week.

**Punishing the silent player** — the ticket's own proposal, a reliability hit falling short of a
no-show's −18. Refused; see [ADR-0049](0049-an-unscored-match-is-an-evening-not-evidence.md).

## Consequences

**One transition is retargeted, one is re-timed, and the model stays at 33 situations.** In the
post-play group the deadline rung and the score-exists rung swap order:
`confirmResult` is now tested first and no longer falls to `playedNoScore` when a clock runs out —
it resolves to `completed`. `needsResult` → `playedNoScore` survives, moved from `matchEnd + 30 min`
to `matchEnd + 24 h`. No situation is added or removed, and `resultWindow` as a single constant is
replaced by two: an **entry deadline** on the match and a **proposal deadline** on each proposal.

**A card outliving its match is now ordinary.** `keepUntil` is `matchEnd + 24 h` and a result may
settle as late as 48 hours after the final point, so a match awaiting an answer must stay on Now
until it settles and only then begin its 24 hours. Anything that walks matches to clean them up
will strand live results unless it reads settlement rather than the clock.

**The named cost: a loser can still force a no-result.** Counter with any different score, then go
quiet, and the match is uncounted. This is inherent — the only way to close it is to arbitrate,
which we have refused — and what changed is the price. Under the old rule Marta stayed silent and
nobody ever knew. Under this one she must put a score she does not believe in front of the three
people she played, and it is recorded as its own announcement
([ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)). It is visible, so if it becomes a
pattern we can see it; nothing is built to watch for it today.

**A late counter is worse for its author than silence would have been.** Objecting at hour 23
almost certainly ends in no result, where saying nothing would have counted the match. That is
genuinely perverse, it is the weakest point in the design, and it is the one thing worth measuring
once real matches are running.

**The prompt reaches nobody who has not opened the app.** In-app only was chosen deliberately for
the first version — no push and no scheduled local reminder — which is affordable *only* because
the deadline is 24 hours rather than 30 minutes. Shortening the window without a notification
channel would reintroduce the discarded-match problem the ADR was written to remove.

**The match holds four facts and no list** — the result on the table, which side proposed it,
whether it is agreed, and how many proposals have been made. Superseded proposals live as
announcements, not as history on the match, which is what keeps
[ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md) intact. Note the ticket's original
wording said the count *records and does not cap*; it now caps at one per side.
