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
 * | `join` | an Anyone group they are not in — one tap and they are in — or an official group they run |
 * | `ask` | a People I approve group — the tap leaves a Join request |
 * | `requested` | they asked, and the request is waiting |
 * | `in` | they are a Group member |
 *
 * A declined request reads `NONE` on the wire, so it comes back as `ask` with nothing said.
 *
 * **An Administrator acting as a player always joins the groups they run directly** (ADR-0183 §7):
 * they would otherwise be asking themselves. That holds over a request they left before the club
 * made them its administrator too — their own *Join* admits them (#509) — so the only word that
 * outranks it is *you're in*.
 */
export type GroupAction = 'join' | 'ask' | 'requested' | 'in';

export function groupAction(
  group: Pick<GroupAtClub, 'relation' | 'joinPolicy' | 'isAdministrator'>,
): GroupAction {
  switch (group.relation) {
    case 'MEMBER':
      return 'in';
    case 'REQUESTED':
      return group.isAdministrator ? 'join' : 'requested';
    case 'NONE':
      return group.isAdministrator || group.joinPolicy === 'ANYONE' ? 'join' : 'ask';
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
