/**
 * **Every sentence Groups, New group, Join a group and the group page compose from a value** —
 * and every name a control is spoken by. The fixed sentences are `groupsCopy.ts`, re-exported
 * here; copy is code, and nothing is inlined in a component.
 *
 * Taken from the mocks (play 1, 3–13, 23–40), with the mocks' *Rakieta* read as **Raketa**
 * (ADR-0187 §8). Two rules sit over it:
 *
 * - **A name is said whole.** The *approves joins* line carries the Owner's whole Name and the
 *   row truncates the line, as it truncates any line; no first name is cut from it here or on the
 *   server (ADR-0171 §4, #505).
 * - **A counted phrase goes through `counted()`**, so *1 member* is never *1 members* and a market
 *   with real plural rules has one function to change.
 */

import { sportLabel } from '@/features/onboarding/types';
import { counted } from '@/shared/formatting/counted';
import { formatDistanceKm } from '@/shared/formatting/ratingFormat';

import { GROUP_NAME_MAX, type GroupAtClub, type SearchedClub } from '../domain/group';
import type { GroupAction } from '../domain/groupRules';

import { GROUPS_COPY } from './groupsCopy';

export { GROUPS_COPY };

/** The separator every composed line in this feature uses — the mocks' middle dot. */
const DOT = ' · ';

/** *No club called "perr"* — home-club search's empty answer, quoting what was searched for. */
export function noClubCalled(text: string): string {
  return `No club called “${text}”`;
}

/** *No match for "co"* — join search's empty answer for text. */
export function noMatchFor(text: string): string {
  return `No match for “${text}”`;
}

/** *Games picked for this group start with courts at Bonarka Arena…* — once a club is chosen (play 11). */
export function chosenClubConsequence(clubName: string): string {
  return `Games picked for this group start with courts at ${clubName}. When their courts are booked, courts from other clubs are offered.`;
}

/** *8 members* */
export function membersLine(count: number): string {
  return counted(count, 'member', 'members');
}

/** *1 member · Bonarka Arena* — the group page's second line (play 40). */
export function membersAtClub(count: number, clubName: string): string {
  return `${membersLine(count)}${DOT}${clubName}`;
}

/** *anyone can join*, or *Karol Nowak approves joins* — who answers a request. */
export function approverLine(group: Pick<GroupAtClub, 'joinPolicy' | 'ownerName'>): string {
  if (group.joinPolicy === 'ANYONE') return 'anyone can join';
  return `${group.ownerName ?? 'the owner'} approves joins`;
}

/** *11 members · Coach Andrzej approves joins* — a group row's second line (play 9, 35). */
export function groupRowMeta(group: GroupAtClub): string {
  return `${membersLine(group.memberCount)}${DOT}${approverLine(group)}`;
}

/** *Tennis, Padel* — a club's sports, in the order the club serves them. */
function sportsList(sports: SearchedClub['sports']): string {
  return sports.map(sportLabel).join(', ');
}

/**
 * *Grzegórzki · 2,4 km · Tennis, Padel* — a club's line under its name.
 *
 * The distance is drawn only where the row draws one — Join a group's club cards and the chosen
 * home club do, home-club search's rows do not (#512) — and **never for a reader with no Location
 * area**, whose clubs come A–Z with `null` for a distance (story 28).
 */
export function clubLine(club: SearchedClub, { distance }: { readonly distance: boolean }): string {
  const parts = [club.district];
  if (distance && club.distanceKm !== null) parts.push(formatDistanceKm(club.distanceKm));
  if (club.sports.length > 0) parts.push(sportsList(club.sports));
  return parts.join(DOT);
}

/** What each group action says — the button's word, or the tag in its place. */
export const ACTION_WORD: Readonly<Record<GroupAction, string>> = GROUPS_COPY.action;

/**
 * What a group row's action is **called** — the group's name rides with it, so two rows' *Join*s
 * are two names. The two taps say their own word; the two states say theirs after the name.
 */
export function actionLabel(action: GroupAction, groupName: string): string {
  switch (action) {
    case 'join':
    case 'ask':
      return `${ACTION_WORD[action]} ${groupName}`;
    case 'requested':
    case 'in':
      return `${groupName}: ${ACTION_WORD[action]}`;
  }
}

/**
 * **A create the form can name the refusal of** — the server checks the name, then the club, in
 * the form's order. The name's limit is the domain's, so the sentence cannot state another.
 */
export const CREATE_REFUSALS = {
  group_name_invalid: `Give the group a name of up to ${GROUP_NAME_MAX} characters.`,
  home_club_unknown: 'That club isn’t in Raketa any more. Pick another home club.',
} as const satisfies Readonly<Record<string, string>>;

/** A card on the Groups list, spoken: name, size, sports and home club. */
export function groupCardLabel(group: {
  readonly name: string;
  readonly memberCount: number;
  readonly sports: SearchedClub['sports'];
  readonly homeClub: { readonly name: string };
}): string {
  const plays = group.sports.length > 0 ? [`plays ${sportsList(group.sports)}`] : [];
  return [group.name, membersLine(group.memberCount), ...plays, group.homeClub.name].join(', ');
}

/** A home-club search row, spoken — the whole row is the one tap, and the amber is said in words. */
export function setAsHomeLabel(club: SearchedClub): string {
  const here = club.groups.length > 0 ? [GROUPS_COPY.newGroup.groupAlreadyHere] : [];
  return [`Set ${club.name} as home club`, clubLine(club, { distance: false }), ...here].join(', ');
}

/** A club's card header in Join a group, spoken — context, not a button (story 39). */
export function clubCardLabel(club: SearchedClub): string {
  return `${club.name}, ${clubLine(club, { distance: true })}`;
}

/** The chosen home club's card, spoken. */
export function chosenClubLabel(club: SearchedClub): string {
  return `Home club: ${club.name}, ${clubLine(club, { distance: true })}`;
}
