/**
 * **What a player may do about a result, and what the screen is therefore drawing.**
 *
 * One route takes three acts and the record decides which — *"a client that named which would
 * be a client that could name it wrongly, and a mislabelled correction is a proposal nobody may
 * make"*. So nothing here chooses a request. What it chooses is a **screen**, and the ticket
 * names why that matters: a correction and a counter are the same `POST` and completely
 * different news, and *"a player will spend an attempt fixing a typo"* unless the difference is
 * visible before the tap.
 *
 * Seven states, folded from the standing, the standing proposal and which seat is yours.
 *
 * | Standing | Whose score stands | The screen |
 * | --- | --- | --- |
 * | `AWAITING_ENTRY` | — | the entry, and when it stops being sayable |
 * | `NEVER_PLAYED` | — | a ghost: nothing to do, and nobody marked for it |
 * | `AWAITING_ANSWER` | yours | free correction, and the hour silence agrees |
 * | `AWAITING_ANSWER` | theirs | agree, or disagree **with a score** |
 * | `AWAITING_ANSWER` | both | the disagreement this platform does not arbitrate |
 * | `CONFIRMED` | — | the agreed score, and what it said about you |
 * | `UNSCORED` | — | an evening, not evidence |
 *
 * ## `both-stand` is read off the standing and never off the missing proposal
 *
 * `standing_proposal` is absent in two cases that mean opposite things, and the schema says so:
 * nothing has been entered, or **both sides have spoken**. The standing tells them apart, and a
 * client that inferred *nothing entered* from the absence would draw the entry control over a
 * game in the middle of an argument.
 *
 * ## Two contract gaps are recorded here, and neither is a rule this feature invented
 *
 * **1. Nothing is offered on `both-stand`.** The aggregate allows an acceptance there — either
 * side may accept the other's, which is the only way out of a two-proposal disagreement, and
 * ADR-0137 §4 keeps it — and **the wire returns neither score in that state**: `score` is the
 * agreed one and is absent, and `standing_proposal` is *"when exactly one is"*. So the client
 * could offer the act only by asking somebody to agree with a score it cannot show them, which
 * is worse than not offering it. The copy states what happens now and promises no control.
 * **Two proposals crossing on the response would close it**, and until they do this flow's one
 * documented exit is unreachable from a client.
 *
 * **2. A pending acceptance is invisible.** `GameSchema` carries no acceptance, and
 * `standing_of` returns `AWAITING_ANSWER` for the whole six-hour grace after one — so the
 * proposing side goes on being told *if nobody answers, this stands*, and goes on being offered
 * a correction the aggregate will refuse with `the_other_side_has_answered`. This side cannot
 * fold the grace: nothing on the response says an acceptance happened. What the client does
 * instead is refuse to guess — the refusal's own sentence says only that the other side has
 * answered, and **never when**, because *while you were typing* would be hours wrong.
 * **An acceptance and its `settles_at` on `GameSchema` would close it.**
 */

import type { Game, Score, StandingProposal } from './game';
import type { GameSide, Outcome } from './vocabulary';

/** The one act a screen state offers, in the order the screen draws them. */
export type ResultAct = 'enter' | 'correct' | 'accept' | 'counter';

export type ResultConversation =
  /** No seat of this game is yours. The client half of `you_were_not_on_this_court`. */
  | { readonly kind: 'not-yours' }
  /**
   * A standing this build has no word for. It draws `OUT_OF_DATE_GAP` and offers nothing:
   * acting on a game whose state we cannot name is how a correction becomes a second proposal.
   */
  | { readonly kind: 'unreadable' }
  | { readonly kind: 'awaiting-entry'; readonly entryClosesAt?: string }
  | { readonly kind: 'never-played' }
  | { readonly kind: 'ours-stands'; readonly proposal: StandingProposal }
  | { readonly kind: 'theirs-stands'; readonly proposal: StandingProposal }
  | { readonly kind: 'both-stand' }
  | { readonly kind: 'confirmed'; readonly score?: Score; readonly outcome?: Outcome }
  | { readonly kind: 'unscored' };

/**
 * Which side of the net is yours — **a join, not a rule.**
 *
 * `SeatingSchema` carries a side and a player id and states no `Relationship`, unlike the
 * arrangements a builder reads, so the answer is a lookup of your own id in a frozen court.
 * `undefined` when no seat is yours, which the list cannot produce and a link can.
 */
export function sideOf(game: Game, playerId: string): GameSide | undefined {
  return game.seats.find((seat) => seat.playerId === playerId)?.side;
}

/** Everybody on your side but you, and everybody across the net. Sides, because nobody is named. */
export function courtSizes(game: Game, side: GameSide) {
  const ours = game.seats.filter((seat) => seat.side === side).length;
  return { ours, theirs: game.seats.length - ours };
}

/** What this game is asking of this player, right now. */
export function resultConversation(game: Game, playerId: string): ResultConversation {
  const side = sideOf(game, playerId);
  if (side === undefined) return { kind: 'not-yours' };

  if (game.standing === undefined) return { kind: 'unreadable' };

  switch (game.standing) {
    case 'AWAITING_ENTRY':
      return { kind: 'awaiting-entry', entryClosesAt: game.entryClosesAt };
    case 'NEVER_PLAYED':
      return { kind: 'never-played' };
    case 'CONFIRMED':
      return { kind: 'confirmed', score: game.score, outcome: game.outcome };
    case 'UNSCORED':
      return { kind: 'unscored' };
    case 'AWAITING_ANSWER': {
      const proposal = game.standingProposal;
      if (proposal === undefined) return { kind: 'both-stand' };
      return proposal.side === side
        ? { kind: 'ours-stands', proposal }
        : { kind: 'theirs-stands', proposal };
    }
  }
}

/**
 * Which act a grid opened on this state would send — **`undefined` where no grid may open.**
 *
 * The screen never names the act on the request, and it does have to name it in two places a
 * player reads: the send's own word, and whether opening the grid is *entering* or *answering*.
 * That is a rule about the state rather than about the screen, so it lives here beside the one
 * that says which controls exist at all.
 */
export function editingAct(
  conversation: ResultConversation,
): 'enter' | 'correct' | 'counter' | undefined {
  switch (conversation.kind) {
    case 'awaiting-entry':
      return 'enter';
    case 'ours-stands':
      return 'correct';
    case 'theirs-stands':
      return 'counter';
    default:
      return undefined;
  }
}

/**
 * The acts this state offers, **in the order the screen draws them**.
 *
 * `accept` leads `counter` because agreeing is the ordinary answer and disagreeing is the one
 * that has to carry a score — and because *"there is no bare rejection"* means the second
 * control is never the cheap one.
 */
export function actsOffered(conversation: ResultConversation): readonly ResultAct[] {
  switch (conversation.kind) {
    case 'awaiting-entry':
      return ['enter'];
    case 'ours-stands':
      return ['correct'];
    case 'theirs-stands':
      return ['accept', 'counter'];
    case 'not-yours':
    case 'unreadable':
    case 'never-played':
    case 'both-stand':
    case 'confirmed':
    case 'unscored':
      return [];
  }
}
