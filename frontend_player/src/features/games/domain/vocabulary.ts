/**
 * The words `games` is spoken to this app in — **codes, and never sentences**.
 *
 * Nine of them are a standing, six are what became of a player somebody said was not here yet,
 * two are what kind of evening it was, two are a side of the net and two are what a confirmed
 * result says about you. Every one is the backend's own vocabulary
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
 * **Derived from the record and the clock and never stored**, which is why there are nine of them
 * and not a status column: a full game whose entry window ran out with nobody recording it reads
 * `PLAYED_NO_SCORE` whether or not anything has swept it, *because nothing sweeps it*
 * ([ADR-0137](../../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) §2,
 * as amended by ADR-0195). Three are waits and the rest are ends, and the client may not fold
 * another. **`CALLED_OFF` is an act rather than a fold**
 * ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)): somebody
 * ended a game a seat had been left on, and it is not an evening, so nothing anybody is measured
 * on moves.
 */
export type GameStanding =
  | 'AWAITING_ENTRY'
  /**
   * A **full** booked game whose entry window closed with no score and nobody *Didn't come* (#655;
   * ADR-0195 §2): played, for everybody on it, and no Level moves. It replaced *Never played* — a
   * booked, paid, full court is the evidence that it was played.
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
   * Two scores named **different winners** and neither side agreed with the other's before the later
   * one's answer window closed (#654; ADR-0195 §5): no Level moves. Rakieta does not decide who won.
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
   * Somebody on a booked game's court was tapped *isn't here yet* in its first half hour and has not
   * arrived (#657; ADR-0195 §3) — a wait, like a score on the table. **No score is taken while it
   * holds**: their arrival, or the half hour running out, ends it.
   */
  | 'NOT_HERE_YET'
  /**
   * Somebody tapped *isn't here yet* never arrived by half an hour after the start (#657): the game
   * takes no score and never counts. For a day it is provisional — their *I was there*, confirmed by
   * somebody else on the court, makes them Came late, and the game carries on.
   */
  | 'DIDNT_COME';

/**
 * **What became of one player somebody said was not here yet** (#657; ADR-0195 §3) — folded by the
 * backend against `read_at`, never stored, and never folded here.
 *
 * - `WAITING` — tapped, not arrived, and the half hour still runs.
 * - `ON_TIME` — arrived within ten minutes of the start: nothing is recorded, and the tap vanishes.
 * - `CAME_LATE` — arrived ten to thirty minutes after the start.
 * - `DIDNT_COME` — no arrival by half an hour after the start: provisional until the late claim's
 *   day ends, final after it.
 * - `CLAIMED` — said *I was there*, and nobody has confirmed it yet: still *Didn't come* until then.
 * - `CONFIRMED` — *I was there*, confirmed by somebody else on the court: **Came late**.
 */
export type AttendanceState =
  'WAITING' | 'ON_TIME' | 'CAME_LATE' | 'DIDNT_COME' | 'CLAIMED' | 'CONFIRMED';

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
