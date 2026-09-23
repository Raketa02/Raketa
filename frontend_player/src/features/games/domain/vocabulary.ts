/**
 * The words `games` is spoken to this app in — **codes, and never sentences**.
 *
 * Six of them are a standing, two are what kind of evening it was, two are a side of the net
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
 * **Derived from the record and the clock and never stored**, which is why there are six of
 * them and not a status column: a game whose entry window ran out reads as never played whether
 * or not anything has swept it, *because nothing sweeps it*
 * ([ADR-0137](../../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) §2).
 * Four are ends and two are waits, and the client may not fold a seventh. **`CALLED_OFF` is the
 * fourth end** ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)):
 * an act rather than a fold — somebody ended a game a seat had been left on — and neither an
 * evening nor a ghost, so nothing anybody is measured on moves. Its card and its shelf life are
 * [#419](https://github.com/Raketa02/Raketa/issues/419)'s; what is here is the word the contract
 * demands.
 */
export type GameStanding =
  'AWAITING_ENTRY' | 'NEVER_PLAYED' | 'AWAITING_ANSWER' | 'CONFIRMED' | 'UNSCORED' | 'CALLED_OFF';

/**
 * Whether this evening is evidence.
 *
 * **Stamped when the game was arranged and never derived at the end.** A game nobody scored
 * stays `COUNTED`, because *a friendly is a thing people choose* — the whole of ADR-0049's
 * fourth rejected option, and the reason one word never grows two meanings here.
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
