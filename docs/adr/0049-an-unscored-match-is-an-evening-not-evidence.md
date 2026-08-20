# ADR-0049 — An unscored match is an evening, not evidence

- **Status:** Accepted
- **Date:** 2026-08-20
- **Withdraws:** the Player Score movements attached to the post-play group by `3.1` §1.4 and
  `rakieta-now-section-specification.md` §351–356

## Context

[ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md) makes a match
countable without anybody agreeing to it, which leaves two questions the specification answered
under the old rule and answered wrongly under the new one: **what a player loses by not acting**,
and **what a match with no result actually is**.

The shipped answers are that all four players lose a point of Player Score when nobody enters a
score — *"it is a shared job"* — and that a match with no confirmed score is `playedNoScore`,
*"counts for nobody"*, with the specification set nowhere saying what that means for anything
except the level.

Two facts make both answers hard to keep. **Nothing on Player Score is about scoring.** Its four
strands are attendance, late cancellations, payment failures and replacement success; its
published promise is *"what clears it: turning up — nothing else"*; and
`backend/app/engines/matchmaking.py` defines the number as *the fraction of the matches this
player committed to that they actually played*. A player who turned up, played and paid scores
full marks on it, and should. **And `friendly` is already a word here that means something else:**
a match is created as **counted** or as a **friendly**, a player may declare which kind they want,
and the fit engine scores the mismatch at 0,30 because *"a friendly and a rated match are
different activities with the same equipment."*

## Decision

**No player is penalised for not entering or not agreeing a result.** Not the silent loser, not
the four who all went home, not the side whose counter went unaccepted. Player Score keeps its
four strands and its promise.

**A match with no agreed result is a counted match that produced no result.** It is never
reclassified as a friendly.

**It counts as an evening and never as evidence.** It appears in history and in how much a player
has played; it establishes that these people have now played together; **it moves nobody's level
and tells the rating context nothing about how good anybody is.**

## Considered options

**The reliability hit the ticket proposed** — smaller than a no-show's −18, possibly forgiven on a
first occurrence. Refused on its own terms: the reason to punish Marta was that staying silent
used to be free *and profitable*, because it protected her level.
[ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md) removed the profit
— her level moves whether she taps or not — so there is no incentive left to price, and what
remains is a fine for not opening an app that **cannot ring her**: Raketa sends nothing to a phone,
so a dead battery and simple inattention are the same event to us. If players are later observed
confirming scores they believe are wrong in order to avoid a mark, that is a reason to add one,
with evidence.

**Landing it on the existing turning-up number** rather than as a new strand. Refused outright and
worth recording, because it is the cheap implementation and it corrupts the one number that
decides whether a player may join a match at all: it would let somebody with a perfect attendance
record be marked as unreliable *at showing up*, and two engines read that number.

**Keeping the shared −1 when nobody enters anything.** It survives longer than the others — nobody
acted, so there is no unfairness in charging everyone — and it still loses. Its job was to make
somebody reach for their phone inside thirty minutes, and with the deadline now 24 hours it is
charging a group for missing a prompt most of them never saw. The four of them already lost the
thing they came for: an evening that produced no evidence about any of them.

**Calling it a friendly.** Rejected: a friendly is a thing people *choose*. Reclassifying a counted
match because nobody typed a score hands a player the exact evening they declared they did not
want, and gives one word two meanings — what you chose, and what you failed to record.

## Consequences

**The result flow has no sanctions at all**, which is unusual in this model — a no-show is −18, a
late cancellation costs, an unfilled seat forfeits. Every incentive here is structural instead: the
only way to protect your level from a result is to state a different score in front of the people
you played, and the only way to lose evidence is to lose it for everyone including yourself.

**Playing and proving are now separate facts about the same match**, and both must be readable. A
player's count of matches played, who they have played with, and how recently they were on court
all include unscored matches; nothing the rating context reads does. Any query that treats "played"
and "counted" as one thing will be wrong for this case.

**`playedNoScore` keeps its name and its situation** and loses its consequence sentence. The tag
and copy stay client-owned; what changes is that the line about all four losing a point is
withdrawn rather than reworded.

**Player Score remains unmodelled and untouched by this work.** It has no entry in root
`CONTEXT.md`, ships dark in every Match Fit snapshot, and this ADR deliberately adds nothing to it.
Its first real definition is still owed by whoever builds it.
