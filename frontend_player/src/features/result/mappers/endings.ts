/**
 * The two situations that end the conversation, and what each one says about it.
 *
 * `ADR-0060`: *"the route renders by situation, not by a screen identifier"*, and
 * this is the one place that is literally true — every other block on the screen is
 * composed from a server boolean, a score or a clock. An ending is what is left
 * when there is nothing to do and no clock to watch, and the two of them say
 * opposite things, so neither can be derived from the absence of the other.
 *
 * **A partial table, on purpose.** Thirty-four of the thirty-six situations end
 * nothing — a forming match reaches this route and resolves to its own forming
 * situation with an empty result block, which is dull and correct — and writing
 * thirty-four `undefined` rows would be thirty-four rows somebody could get wrong.
 * That is the shape the backend's own act table settled on for the same reason. The
 * assertion beside it is what keeps it honest: `copyTables` writes the two keys out,
 * so a third ending is a decision somebody makes in a diff rather than a row that
 * quietly never appears.
 *
 * **The settled ending is deliberately silent about levels.** No engine produces a
 * level movement, so a screen that mentioned one — in either direction — would be
 * describing a system that does not run. The **unscored** ending does say it, and
 * that asymmetry is `ADR-0060`'s own instruction: that rendering exists to say
 * *"what the evening counted for and what it did not"*, and *nobody's level moved*
 * is the half a player who missed a deadline is actually looking for.
 */

import type { EndingCopy } from '../domain/presentation';

import type { AssertTrue, IsClosedUnion, Situation } from './codes';

/**
 * A settled result, which is final — and which says nothing about anybody's level.
 *
 * No engine produces a level movement, so a screen that mentioned one in either
 * direction would be describing a system that does not run.
 */
const SETTLED: EndingCopy = {
  title: 'Settled',
  lines: ['This result is agreed and final. There is nothing left to answer.'],
};

/**
 * The unscored ending — the fourth of the sentences
 * `deltas/result-confirmation.md` §10 calls weighty, *"the sentence a player reads
 * when their match ended up counting for nothing"*.
 *
 * `ADR-0060` fixes its content exactly: *"what the evening counted for (history,
 * how much a player has played, who they have now played with) and what it did not
 * (nobody's level moved, nobody was penalised, it was not a friendly)"* — which is
 * `ADR-0049` in the words a player reads. Both halves ship: the reassurance is the
 * half a player who missed a deadline is actually looking for, and the sanctions
 * that used to sit here were **withdrawn** rather than softened.
 */
const UNSCORED: EndingCopy = {
  title: 'Nobody entered a score',
  lines: [
    'It counts as an evening: it is in your history, it counts towards how much you have played, and it records that you have now played with these people.',
    'Nobody’s level moved, nobody was penalised, and it was not a friendly — it was a match that produced no result.',
  ],
};

export const ENDING_COPY: Readonly<Partial<Record<Situation, EndingCopy>>> = {
  completed: SETTLED,
  playedNoScore: UNSCORED,
};

/** Fails to compile if `Situation` ever arrives as a bare string. */
export type SituationIsClosed = AssertTrue<IsClosedUnion<Situation>>;

/**
 * How this situation ends, or `undefined` for one that does not end anything.
 *
 * **The argument is a `string` on purpose**, the same as the situation table's: a
 * thirty-seventh situation must cost an installed phone nothing but a block it never
 * had, and typing the parameter as `Situation` would make that path unreachable in
 * the one place it has to work.
 *
 * **Own properties only.** Indexing a `Record` with an arbitrary string reaches
 * `Object.prototype`, and this one is indexed with an arbitrary string on purpose —
 * without the guard a wire value spelled `toString` resolves to a function and the
 * block draws whatever that stringifies to, which is the one failure worse than a
 * missing block.
 */
export function endingCopy(situation: string): EndingCopy | undefined {
  return Object.prototype.hasOwnProperty.call(ENDING_COPY, situation)
    ? (ENDING_COPY as Readonly<Record<string, EndingCopy | undefined>>)[situation]
    : undefined;
}
