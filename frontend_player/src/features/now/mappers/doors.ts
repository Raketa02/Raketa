/**
 * The two sentences the door shows, and the one thing it does.
 *
 * A player who taps a chip for a sport she holds no rating at is owed a
 * destination rather than a better sentence (`ADR-0084`), and the server
 * composes that destination as a **block in the shelves list**, in the position
 * the ranked shelves would occupy. What crosses the wire is a code; the words
 * are this app's, exactly as a shelf's title is.
 *
 * **The block carries no sport**, deliberately: she named it on the request and
 * still holds it, and a second copy on the answer is a second thing that can
 * disagree. So an entry is a function of the chip the client is holding, the
 * same shape `findPreFilter` uses to put a shelf's claim and the selected sport
 * together.
 *
 * **Two codes, one destination.** `noRunYet` and `runParked` differ in what they
 * say and in nothing else — see `DoorCopy` for why the client is not allowed to
 * learn the difference.
 */

import type { DoorCopy } from '../domain/presentation';

import type { AssertTrue, DoorCode, IsClosedUnion, SportFilter } from './codes';
import { SPORT_CHIP_COPY } from './sportBar';

/** The chip the client is holding. The door's block carries no sport of its own. */
export interface DoorContext {
  readonly sport: SportFilter;
}

export type DoorEntry = (context: DoorContext) => DoorCopy;

/**
 * The sport this door is about, in the words the chip above it uses.
 *
 * `all` resolves — server-side — to *the sports she holds a rating at*, so it
 * names no sport she is unrated at and the server never composes a door under
 * it. The fallback is therefore unreachable on a composed screen and exists
 * because *"All"* is not a noun a sentence can take: naming the chip would print
 * **Take the All questions**. It is a word chosen for a sentence, not a rule
 * about when a door appears — the server decides that and this cannot.
 */
function named(sport: SportFilter): string {
  return sport === 'all' ? 'this sport' : SPORT_CHIP_COPY[sport].label;
}

/**
 * Total over the two codes the contract names.
 *
 * Named for the **fact** and not for the words, like every code in this layer:
 * *has she started* is what the server knows, and the copy changes without a
 * backend release.
 */
export const DOOR_COPY: Readonly<Record<DoorCode, DoorEntry>> = {
  noRunYet: ({ sport }) => ({
    line: `We have not placed you at ${named(sport)} yet. A couple of minutes of questions is all it takes.`,
    action: `Take the ${named(sport)} questions`,
  }),
  runParked: ({ sport }) => ({
    line: `Your ${named(sport)} questions are waiting where you left them.`,
    action: 'Pick up where you left off',
  }),
};

/** Fails to compile if `DoorCode` ever arrives as a bare string. */
export type DoorCodeIsClosed = AssertTrue<IsClosedUnion<DoorCode>>;

/**
 * What this door says, or `undefined` for a code this build has never heard of.
 *
 * Typed to take a `string` for the same reason every other lookup in this layer
 * is: an installed phone meeting a third code is the one case a typecheck never
 * reaches, and a door it cannot word is one it draws nothing for — which is the
 * shelves list losing one entry, exactly as `ADR-0084` intends an old build to
 * behave.
 */
export function doorCopy(code: string, context: DoorContext): DoorCopy | undefined {
  const entry: DoorEntry | undefined = (
    DOOR_COPY as Readonly<Record<string, DoorEntry | undefined>>
  )[code];
  return entry === undefined ? undefined : entry(context);
}
