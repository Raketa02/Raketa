/**
 * **Every sentence Groups, New group, Join a group and the group page compose from a value** —
 * and every name a control is spoken by. The fixed sentences are `groupsCopy.ts`, re-exported
 * here; copy is code, and nothing is inlined in a component.
 *
 * Taken from the mocks (play 1, 3–17, 23–55), with the mocks' *Rakieta* read as **Raketa**
 * (ADR-0187 §8). Two rules sit over it:
 *
 * - **A name is said whole.** The *approves joins* line carries the Owner's whole Name and the
 *   row truncates the line, as it truncates any line; no first name is cut from it here or on the
 *   server (ADR-0171 §4, #505).
 * - **A counted phrase goes through `counted()`**, so *1 member* is never *1 members* and a market
 *   with real plural rules has one function to change.
 */

import { sportLabel } from '@/features/onboarding/types';
import { courtSummaryLabel, seatLabel, type SeatPlace } from '@/features/play/types';
import { counted } from '@/shared/formatting/counted';
import { formatDistanceKm, formatLevel } from '@/shared/formatting/ratingFormat';
import type { Sport } from '@/shared/vocabulary/sport';

import { GROUP_NAME_MAX, type GroupAtClub, type SearchedClub } from '../domain/group';
import type { GamesCard } from '../domain/groupPage';
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

// ---------------------------------------------------------------------------
// The group page (#513)
// ---------------------------------------------------------------------------

/**
 * *Sport: Padel* — the fast filter's pill, spoken. The same name for the plain label a player
 * rated in one sport gets, which says the sport and offers nothing to unfold.
 */
export function sportPillLabel(sport: Sport): string {
  return `Sport: ${sportLabel(sport)}`;
}

/** *padel*, inside a sentence — the mocks write a sport in lower case mid-line (play 14–17). */
function sportInLine(sport: Sport): string {
  return sportLabel(sport).toLowerCase();
}

/** The Games card's headline: *Just you so far*, *3 of 4*, or *Nothing picked right now*. */
export function gamesHeadline(card: GamesCard): string {
  switch (card.kind) {
    case 'just-you':
      return GROUPS_COPY.games.justYou;
    case 'filling':
      return `${card.rated} of ${card.seats}`;
    case 'nothing-picked':
      return GROUPS_COPY.games.nothingPicked;
  }
}

/**
 * *The app picks games here once 4 who play padel are in and a court at Bonarka Arena is free…*
 * — what the app is waiting for (story 61). **Not said once the seats could be filled**: what it
 * would wait for then is not people, and the headline already says nothing is picked.
 */
export function gamesLine(card: GamesCard, sport: Sport, clubName: string): string | undefined {
  if (card.kind === 'nothing-picked') return undefined;
  return `The app picks games here once ${card.seats} who play ${sportInLine(sport)} are in and a court at ${clubName} is free. Send the link — it all starts when they arrive.`;
}

/**
 * *Padel, 1 of 4 seats filled.* — a court's seats, spoken as one element before any seat: the
 * Friends court's summary and the Games card's row of seats alike. It is play's sentence
 * (`courtSummaryLabel`, the-words §20.4), so a group's court and a line-up's say the same thing.
 */
export function seatsFilledLabel(sport: Sport, filled: number, seats: number): string {
  return courtSummaryLabel({ sportName: sportLabel(sport), filled, seats });
}

/**
 * *Your side, you, level 2,71* — the reader's seat on the Friends court: play's seat sentence, and
 * the Level the seat draws under the face, in the words play's seats say a Level in.
 */
export function yourSeatLabel(place: SeatPlace, level: number | undefined): string {
  const seat = seatLabel(place, { kind: 'you' });
  return level === undefined ? seat : `${seat}, level ${formatLevel(level)}`;
}

/** *Their side, empty* — a seat a friend could fill, named by where it is (play's `seatLabel`). */
export function emptySeatLabel(place: SeatPlace): string {
  return seatLabel(place, { kind: 'empty', unfilled: null });
}

/** *Padel · 0 of 3 picked* — the Friends screen's eyebrow (play 54), drawn upper case. */
export function friendsPicked(sport: Sport, picked: number, toPick: number): string {
  return `${sportLabel(sport)}${DOT}${picked} of ${toPick} picked`;
}

/** *Friends who join my raketa group with the link show up on this page.* (play 55) */
export function friendsLine(groupName: string): string {
  return `Friends who join ${groupName} with the link show up on this page.`;
}

/**
 * *Join my raketa group on Raketa: https://…* — what Share the link hands the sheet. The link is
 * the whole of what has to arrive; the sentence says what it is to whoever it lands with, in the
 * words the Administrator's WhatsApp post uses (story 128).
 */
export function shareMessage(groupName: string, link: string): string {
  return `Join ${groupName} on Raketa: ${link}`;
}
