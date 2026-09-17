/**
 * **The *Name* row's words** — its title, its live line, and its button
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §27).
 *
 * The screen behind the row is the naming step's form under the tab's chrome, so the boxes'
 * labels and the refusals are the step's and `authErrorMessage`'s, cited. What is this row's
 * own is the line — the name and the handle, which makes the You tab one of the two places
 * the handle is drawn (ADR-0171 §4) — and *Save* where the step says *Continue*.
 */

import { atNickname } from '@/shared/formatting/playerName';

export const NAME_ROW_TITLE = 'Name';

/** `Tomek Kowalski · @tomek.k` — the name every sentence says, and the handle that is theirs alone. */
export function nameLine(name: string, nickname: string): string {
  return `${name} · ${atNickname(nickname)}`;
}

/**
 * *Save*, not *Continue*: the naming from the tab is an edit, and nothing follows it. *Saved*
 * while the boxes are as they opened, as every *Save* on the tab says.
 */
export const SAVE_NAME = { label: 'Save', savedLabel: 'Saved', busyLabel: 'Saving…' } as const;
