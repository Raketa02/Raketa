/**
 * The words `games` is spoken to this app in — **codes, and never sentences**.
 *
 * Ten of them are a standing, two are what kind of evening it was, two are a side of the net
 * and two are what a confirmed result says about you. Every one is the backend's own vocabulary
 * ([ADR-0022](../../../../../docs/adr/0022-kernel-negative-space-and-constant-homes.md)), and
 * the words for them are this feature's — `components/gamePresentation.ts` and nowhere else.
 *
 * These are **spelled here rather than `Extract`ed off the generated union**, for the reason
 * `features/play/domain/vocabulary.ts` gives: the wire boundary keeps `generated/` out of
 * `domain/` and `components/`, so the union that keys a copy table cannot come from transport.
 * What holds the two equal is `mappers/wireVocabulary.ts`, at `pnpm typecheck`, in the one file
 * whose job is saying so — a code added, removed or renamed on the contract fails there and
 * then again in every table that has no words for it.
 */

/**
 * What a game is at the instant it was read.
 *
 * **Derived from the record and the clock and never stored**, which is why there are ten of them
 * and not a status column: a full game whose entry window ran out with nobody recording it reads
 * `PLAYED_NO_SCORE` whether or not anything has swept it, *because nothing sweeps it*
 * ([ADR-0137](../../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) §2,
 * as amended by ADR-0195). Two are waits and the rest are ends, and the client may not fold
 * another. **`CALLED_OFF` is an act rather than a fold**
 * ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)): somebody
 * ended a game a seat had been left on, and it is not an evening, so nothing anybody is measured
 * on moves.
 */
export type GameStanding =
  | 'AWAITING_ENTRY'
  /**
   * A **full** booked game whose entry window closed with no score and nobody marked as not coming
   * (#655; ADR-0195 §2): played, for everybody on it, and no Level moves. It replaced *Never
   * played* — a booked, paid, full court is the evidence that it was played.
   */
  | 'PLAYED_NO_SCORE'
  | 'AWAITING_ANSWER'
  /**
   * The result stands: agreed with by a *That's right*, settled by silence, or — two scores naming
   * the same winner — counted with the closer of them (#654). The wire does not say which, so no
   * sentence here does either.
   */
  | 'CONFIRMED'
  /**
   * A booked game whose every no-show report was disputed. Since #654 two scores never end here
   * (they end `CONFIRMED` or `DISPUTED`), and #657 retires the reports, which leaves it no case.
   */
  | 'UNSCORED'
  /**
   * Two scores named **different winners** and neither side agreed with the other's before the later
   * one's answer window closed (#654; ADR-0195 §5): no Level moves. Raketa does not decide who won.
   */
  | 'DISPUTED'
  | 'CALLED_OFF'
  /**
   * A booked game whose hour came with a seat still open (#544): somebody left after the club's
   * cut-off and nobody took the seat. It takes no result, no Level moves and nobody who stayed is
   * marked for it — *Uncounted · a seat was empty* (the Games & Fill in mechanics §14.1).
   */
  | 'STARTED_SHORT'
  /**
   * Somebody who came to a booked game marked a player who did not (#547, #560), and a report's
   * day to dispute it is still running — a wait, like a score on the table. The game does not
   * count whatever the reports come to (the Games & Fill in mechanics §15.3).
   */
  | 'NO_SHOW_REPORTED'
  /**
   * Every report that stands has had its day undisputed: the game does not count, nobody's Level
   * moves, and not coming is the strongest mark on the record of the player who did not.
   */
  | 'NO_SHOW';

/**
 * Whether this evening is evidence.
 *
 * **Stamped when the game was arranged and never derived at the end.** A game nobody scored
 * stays `COUNTED`, because *a friendly is a thing people choose* — the whole of ADR-0049's
 * fourth rejected option, and the reason one word never grows two meanings here. A `FRIENDLY` is
 * the game the app calls **For fun**, and since #654 it asks nobody anything: its first score is
 * the result the moment it is put up.
 */
export type GameKind = 'COUNTED' | 'FRIENDLY';

/** Which side of the net. **Two, and the game names one of them.** */
export type GameSide = 'A' | 'B';

/**
 * What a confirmed result says about the person reading it.
 *
 * Two values and never a third: an unscored game produces **no outcome for anybody**, and the
 * absence is spelled by the field not being there rather than by a word for it.
 */
export type Outcome = 'WIN' | 'LOSS';

/** The other half of the court. A rule small enough to be wrong in two places if written twice. */
export function otherSide(side: GameSide): GameSide {
  return side === 'A' ? 'B' : 'A';
}

/**
 * A side's half of a set, as `SetScoreSchema` spells it.
 *
 * The wire names the two halves of a set `a` and `b` and the two sides of a net `A` and `B`, and
 * they are **the same fact in two spellings** — so this is the one conversion, rather than a
 * `side === 'A' ? 'a' : 'b'` at each of the four places that needed one. A second lower-case
 * union beside `GameSide` would be that fact typed twice, and a flip is exactly the thing this
 * feature must never get wrong twice.
 */
export type ScoreColumn = 'a' | 'b';

export function scoreColumn(side: GameSide): ScoreColumn {
  return side === 'A' ? 'a' : 'b';
}
