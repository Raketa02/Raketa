/**
 * The half of an ending the wire has no opinion about.
 *
 * The same split Now makes between `domain/presentation.ts` and
 * `mappers/situations.ts`: `domain/` may not name a generated union, so the shape
 * of what a table hands back lives here and the table itself lives one layer out,
 * in the app's declared wire boundary. Pure types and nothing else.
 */

/**
 * What an ended conversation says: a heading, and the sentences under it.
 *
 * A list rather than one string, because the unscored ending is two sentences that
 * do opposite jobs — what the evening counted for, and what it did not — and
 * joining them into a paragraph is what makes the second one easy to drop.
 */
export interface EndingCopy {
  readonly title: string;
  readonly lines: readonly string[];
}
