/**
 * **Reads that list people with the reader's relation to them** — tagged, so a write that moves a
 * relation re-reads every one of them without naming whose they are
 * ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows mechanics §13; architecture
 * Part 7, *A write some other feature's reads depend on*).
 *
 * Home's people rows and their See all (`discovery`) and Hottest groups (`groups`, friends drawn
 * first and counted) each show a person, or a count of them, as the reader stands with them. **Any
 * friend write, and any block, moves that** — from Home, from a record Rankings opened, from a notice,
 * from Members — and `friends` and `blocks` cannot name `discovery`'s keys: `discovery` draws
 * `friends`' button, so the import would run both ways. So a read **declares** that it lists people
 * (`meta: LISTS_PEOPLE`), and the writes **re-read whatever declared it** (`rereadPeopleLists`): only
 * the reads on screen ask the server again, and the rest are marked stale for their next mount.
 *
 * It is a tag on the read, not a key: each feature still owns its keys and its read.
 */

import type { QueryClient } from '@tanstack/react-query';

/** The query `meta` a read lists people under — see the module note. */
export const LISTS_PEOPLE = { listsPeople: true } as const;

/** **Every read that declared `LISTS_PEOPLE`**, invalidated: the ones on screen read again now. */
export function rereadPeopleLists(client: QueryClient): Promise<void> {
  return client.invalidateQueries({ predicate: (query) => query.meta?.listsPeople === true });
}
