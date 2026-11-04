/**
 * **The *Nickname* row's words** — its title and its button
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §27, read through
 * [ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3).
 *
 * The screen behind the row is the naming step's form under the tab's chrome, so the box's label
 * and the refusals are the step's and `authErrorMessage`'s, cited. What is this row's own is its
 * title, and *Save* where the step says *Continue*. Its line is the nickname itself, whole and
 * without an @, as every screen draws it.
 */

export const NICKNAME_ROW_TITLE = 'Nickname';

/**
 * *Save*, not *Continue*: the naming from the tab is an edit, and nothing follows it. *Saved*
 * while the box is as it opened, as every *Save* on the tab says.
 */
export const SAVE_NICKNAME = { label: 'Save', savedLabel: 'Saved', busyLabel: 'Saving…' } as const;
