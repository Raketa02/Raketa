/**
 * **Reads that list people with the reader's relation to them** — tagged, so a write that moves a
 * relation reaches every one of them without naming whose they are
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
 * ## A list that holds still
 *
 * **A row worked out again on every read moves under the thumb** — Home's people rows put the
 * unconnected first, so asking somebody makes them a gap and the next fresh match takes their place
 * (the mechanics §9.1). **A row never changes while the reader looks at it** (§13), so such a read
 * declares that it **holds still** (`holdsPeople`), handing in how to draw a write's answer on what it
 * already read. A friend write hands its answer in (`RelationMoved`: whom, and where the reader now
 * stands with them — the server's answer, never a guess); **every list that holds still draws it on
 * its cards and is marked stale, not read again now**, so the card stays where it was and reads the
 * new relation, and the next read — a return, a pull, foregrounding — works the order out again.
 * Every other list re-reads as before, and so does every list on a write with no answer to hand in: a
 * block, a refusal that is the state moving.
 *
 * It is a tag on the read, not a key: each feature still owns its keys, its read and its cards' shape.
 */

import type { Query, QueryClient } from '@tanstack/react-query';

/** Whom a friend write moved, and where the reader now stands with them — the server's answer. */
export interface RelationMoved<Relation extends string = string> {
  readonly playerId: string;
  readonly relation: Relation;
}

/** The query `meta` a read lists people under — see the module note. */
export const LISTS_PEOPLE = { listsPeople: true } as const;

/**
 * **The query `meta` of a list that holds still** — see the module note. `withRelation` draws a
 * write's answer on the list as read, and leaves everybody else, and the order, as they were.
 */
export function holdsPeople<Data, Relation extends string>(
  withRelation: (data: Data, moved: RelationMoved<Relation>) => Data,
) {
  return { ...LISTS_PEOPLE, withRelation } as const;
}

type WithRelation = (data: unknown, moved: RelationMoved) => unknown;

const listsPeople = (query: Query) => query.meta?.listsPeople === true;

function heldBy(query: Query): WithRelation | undefined {
  const withRelation = query.meta?.withRelation;
  return typeof withRelation === 'function' ? (withRelation as WithRelation) : undefined;
}

/**
 * **Every read that declared `LISTS_PEOPLE`** — invalidated, so the ones on screen read again now;
 * or, given what a friend write moved, **each list that holds still draws it and waits** for its next
 * read (see the module note).
 */
export async function rereadPeopleLists(client: QueryClient, moved?: RelationMoved): Promise<void> {
  if (moved === undefined) {
    return client.invalidateQueries({ predicate: listsPeople });
  }
  const holding = (query: Query) => listsPeople(query) && heldBy(query) !== undefined;
  for (const query of client.getQueryCache().findAll({ predicate: holding })) {
    const withRelation = heldBy(query);
    if (withRelation === undefined || query.state.data === undefined) continue;
    client.setQueryData(query.queryKey, withRelation(query.state.data, moved));
  }
  // After the answer is drawn — writing a query's data clears its stale mark.
  await Promise.all([
    client.invalidateQueries({ predicate: holding, refetchType: 'none' }),
    client.invalidateQueries({ predicate: (query) => listsPeople(query) && !holding(query) }),
  ]);
}
