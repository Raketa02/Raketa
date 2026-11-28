/**
 * **The friends codes, spelled here** — held equal to the generated ones in
 * `mappers/wireVocabulary.ts`, so a code the contract adds or renames fails `pnpm typecheck` in the
 * one file whose job is saying so ([#753](https://github.com/Rakieta02/Rakieta/issues/753); ADR-0202
 * §1–§2).
 *
 * The wire's own spellings, kept, as `groups`' relation to a group keeps its own: every surface that
 * carries the reader's relation to a person — Members' rows, the record — keys its pill, its tag or
 * its buttons by these four.
 */

/**
 * **Where the reader stands with one person** — only the reader's own, on every surface (Q12):
 *
 * - `NONE` — nothing stands between them: **+ Add**, *Add friend*;
 * - `SENT` — the reader asked, and it is open (set aside or not, which is never said): *request
 *   sent*, *Request sent ▾*;
 * - `ASKED_YOU` — they asked the reader: **Accept**;
 * - `FRIEND` — *friend*, *Friend ✓ ▾*.
 */
export type FriendRelation = 'NONE' | 'SENT' | 'ASKED_YOU' | 'FRIEND';

/**
 * **The screen a request is asked from** — which the request keeps, and which its card on the other
 * person's Home names through the group the screen showed. A link's request (#748) is never sent:
 * opening the link makes it. `RANKING` is a record opened from the Rankings page (#773, #779), sent
 * with that page's sport (`recordAskedWhere`). `NEW_PLAYERS` is Home's New in Rakieta row, or a
 * record opened from it (#801; the Home rows mechanics §12): their card reads *Found you among new
 * players*, and the request names neither a group nor a sport. `SAME_LEVEL` is Home's Same
 * competitive level row, or a record opened from it (#802), sent with the card's sport: their card
 * reads *Your level in padel · 91% even*. `SAME_VIBE` is Home's Same vibe row, or a record or vibe sheet
 * opened from it (#803), naming neither a group nor a sport: their card reads *6 things in common*.
 */
export type AskedFrom =
  'MEMBERS' | 'RECORD' | 'RESULT' | 'RANKING' | 'NEW_PLAYERS' | 'SAME_LEVEL' | 'SAME_VIBE';

/**
 * **Which way an open request points** (#754) — the Friends page's two request tabs, each its own
 * read: `ASKED_YOU`, made of the reader, set aside or not, **Accept** on each; `YOU_ASKED`, the
 * reader's own, **Cancel** on each.
 */
export type RequestDirection = 'ASKED_YOU' | 'YOU_ASKED';
