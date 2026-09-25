/**
 * **The groups feature's two rules** — what a group row offers its reader, and which answer a
 * search draws. Pure, so each is stated once and tested without a screen. When a new group may be
 * created is the New group form's schema (`schemas/newGroupForm`).
 */

import type { ClubSearch, GroupAtClub } from './group';

/**
 * **What a group row offers** — the one tap, or the word in its place (stories 41–44).
 *
 * | | |
 * | --- | --- |
 * | `join` | an Anyone group they are not in — one tap and they are in |
 * | `ask` | a People I approve group — the tap leaves a Join request |
 * | `requested` | they asked, and the request is waiting |
 * | `in` | they are a Group member |
 *
 * A declined request reads `NONE` on the wire, so it comes back as `ask` with nothing said.
 */
export type GroupAction = 'join' | 'ask' | 'requested' | 'in';

export function groupAction(group: Pick<GroupAtClub, 'relation' | 'joinPolicy'>): GroupAction {
  switch (group.relation) {
    case 'MEMBER':
      return 'in';
    case 'REQUESTED':
      return 'requested';
    case 'NONE':
      return group.joinPolicy === 'ANYONE' ? 'join' : 'ask';
  }
}

/**
 * **Which answer a search draws** (stories 19, 34, 37, 38). Clubs when it found any; otherwise
 * the empty that matches what was searched for — text that matched nothing, or a link that leads
 * nowhere, which is a dead link rather than a typo and is said differently. A club found with no
 * groups is still a club, and its card says *No groups here yet* itself.
 */
export type SearchOutcome =
  | { readonly kind: 'clubs' }
  | { readonly kind: 'no-match'; readonly text: string }
  | { readonly kind: 'nothing-at-link' };

export function searchOutcome(search: ClubSearch): SearchOutcome {
  if (search.clubs.length > 0) return { kind: 'clubs' };
  return search.readAs === 'LINK'
    ? { kind: 'nothing-at-link' }
    : { kind: 'no-match', text: search.text };
}
