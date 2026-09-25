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
import { playerName } from '@/shared/formatting/playerName';
import { formatDistanceKm, formatLevel } from '@/shared/formatting/ratingFormat';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  GROUP_NAME_MAX,
  type Group,
  type GroupAtClub,
  type GroupMember,
  type SearchedClub,
  type SportLevel,
} from '../domain/group';
import type { GroupExit } from '../domain/groupInfo';
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

// ---------------------------------------------------------------------------
// The Info tab, Members and Edit group (#514)
// ---------------------------------------------------------------------------

/**
 * *raketa.app/join/K7PQ2MXA* — the link as Info's card draws it (play 57, 60): the address
 * without its scheme, which the mocks never print. Spoken, copied and shared whole.
 */
export function linkShown(link: string): string {
  return link.replace(/^https?:\/\//, '');
}

/** *Group link, raketa.app/join/K7PQ2MXA* — the card's link, spoken. */
export function linkLabel(link: string): string {
  return `Group link, ${linkShown(link)}`;
}

/**
 * *anyone can join*, *you approve joins*, *the owner approves joins* — the members row's policy
 * line. The group's read names no Owner, so a member who is not one reads *the owner*, as a row
 * whose Owner can no longer be named does.
 */
export function infoPolicyLine(group: Pick<Group, 'joinPolicy' | 'isOwner'>): string {
  if (group.joinPolicy === 'ANYONE') return GROUPS_COPY.info.anyoneCanJoin;
  return group.isOwner ? GROUPS_COPY.info.youApprove : GROUPS_COPY.info.ownerApproves;
}

/** *+2* — the members row's count of everybody it does not draw. */
export function moreFaces(count: number): string {
  return `+${count}`;
}

/** *8 members, plays Padel, Tennis, anyone can join* — the members row, spoken; it opens Members. */
export function membersRowLabel(
  group: Pick<Group, 'memberCount' | 'sports' | 'joinPolicy' | 'isOwner'>,
): string {
  const plays = group.sports.length > 0 ? [`plays ${sportsList(group.sports)}`] : [];
  return [membersLine(group.memberCount), ...plays, infoPolicyLine(group)].join(', ');
}

/** *Want to join · 2* — the Owner's queue, drawn upper case (club 20). */
export function wantToJoin(count: number): string {
  return `Want to join${DOT}${count}`;
}

/** *Padel 2,44 · Tennis 2,60* — every sport a person asking is rated in, full names (club 20). */
export function requestLevels(levels: readonly SportLevel[]): string {
  return levels.map(({ sport, level }) => `${sportLabel(sport)} ${formatLevel(level)}`).join(DOT);
}

/** A name as a row draws it — the whole Name, or the word for somebody who can't be named. */
export function personName(name: string | null): string {
  return name === null ? playerName({ kind: 'unknown' }) : playerName({ kind: 'player', name });
}

/** *Michał Rogalski, Padel 2,44 · Tennis 2,60* — a request's row, spoken before its two taps. */
export function requestLabel(request: {
  readonly name: string | null;
  readonly levels: readonly SportLevel[];
}): string {
  const levels = request.levels.length > 0 ? [requestLevels(request.levels)] : [];
  return [personName(request.name), ...levels].join(', ');
}

/** *Approve Michał Rogalski* — the tap is named for whom it admits. */
export function approveLabel(name: string | null): string {
  return `${GROUPS_COPY.info.approve} ${personName(name)}`;
}

/** *Decline Michał Rogalski* — the ✕, named for what it does and to whom. */
export function declineLabel(name: string | null): string {
  return `Decline ${personName(name)}`;
}

/**
 * **What the Leave or Delete sheet says** (stories 77–79): a delete that it cannot be undone; a
 * leave, the handover first where the reader owns the group, then the way back in under the
 * group's rule.
 */
export function exitSheetBody(
  exit: GroupExit,
  group: Pick<Group, 'isOwner' | 'joinPolicy'>,
): readonly string[] {
  const copy = GROUPS_COPY.info;
  if (exit === 'delete') return [copy.deleteBody];
  const rejoin = group.joinPolicy === 'ANYONE' ? copy.rejoinAnyone : copy.rejoinAsk;
  return group.isOwner ? [copy.leaveHandover, rejoin] : [rejoin];
}

/** One code for *no such group* and *not one of yours*, met by a write after the group has gone. */
const GROUP_GONE = 'This group isn’t one of yours any more.';

/**
 * **The way out's words, by which way it is** — the door, the sheet's title and close, the act
 * busy, and the toast once it is done. One table, so the two doors cannot be half one and half
 * the other.
 */
export interface ExitWords {
  readonly door: string;
  readonly busy: string;
  readonly title: string;
  readonly close: string;
  readonly done: string;
}

export const EXIT_WORDS: Readonly<Record<GroupExit, ExitWords>> = {
  delete: {
    door: GROUPS_COPY.info.delete,
    busy: GROUPS_COPY.info.deleting,
    title: GROUPS_COPY.info.deleteTitle,
    close: GROUPS_COPY.info.deleteClose,
    done: GROUPS_COPY.info.deleted,
  },
  leave: {
    door: GROUPS_COPY.info.leave,
    busy: GROUPS_COPY.info.leaving,
    title: GROUPS_COPY.info.leaveTitle,
    close: GROUPS_COPY.info.leaveClose,
    done: GROUPS_COPY.info.left,
  },
};

/**
 * **A refused leave or delete, in the sheet's words.** The two conflicts mean the member count
 * moved since the page was read, and each names the other door, which the page now draws.
 */
export const EXIT_REFUSALS = {
  lone_owner_cannot_leave: 'You’re the only one left in the group — delete it instead.',
  group_has_other_members: 'Somebody else is in the group now — leave it instead.',
  not_the_group_owner: 'Only the group’s owner can delete it.',
  group_not_found: GROUP_GONE,
} as const satisfies Readonly<Record<string, string>>;

/** A refused answer to a request — answered from another phone, or a group that changed hands. */
export const REQUEST_REFUSALS = {
  join_request_not_found: 'That request isn’t waiting any more.',
  not_the_group_owner: 'Only the group’s owner answers requests.',
  group_not_found: GROUP_GONE,
} as const satisfies Readonly<Record<string, string>>;

/** A refused save — the name the form can name, and the two it cannot fix. */
export const EDIT_REFUSALS = {
  group_name_invalid: CREATE_REFUSALS.group_name_invalid,
  not_the_group_owner: 'Only the group’s owner can edit it.',
  group_not_found: GROUP_GONE,
} as const satisfies Readonly<Record<string, string>>;

/** *Kazimierz crew · 8* — Members' eyebrow (play 61), drawn upper case. */
export function membersEyebrow(group: Pick<Group, 'name' | 'memberCount'>): string {
  return `${group.name}${DOT}${group.memberCount}`;
}

/** *Play Padel · 8* — the list's heading: the sport, and how many here play it. */
export function playSportCount(sport: Sport, count: number): string {
  return `Play ${sportLabel(sport)}${DOT}${count}`;
}

/** *Padel 2,71 · score 92* — a row's line; no score for somebody with no record, never *score 0*. */
export function memberLine(
  sport: Sport,
  member: Pick<GroupMember, 'level' | 'playerScore'>,
): string {
  const level = `${sportLabel(sport)} ${formatLevel(member.level)}`;
  return member.playerScore === undefined ? level : `${level}${DOT}score ${member.playerScore}`;
}

/** Who a Members row is about, and whether it is the reader's own. */
export interface MemberRowPerson extends Pick<
  GroupMember,
  'name' | 'level' | 'playerScore' | 'isOwner'
> {
  readonly you: boolean;
}

/** *You* for the reader's own row, the whole Name for anybody else (play 61). */
export function memberName(member: Pick<MemberRowPerson, 'name' | 'you'>): string {
  return member.you ? playerName({ kind: 'you' }) : personName(member.name);
}

/** *Karol Tomczak, admin, Padel 2,75 · score 93* — a row, spoken as it is drawn. */
export function memberRowLabel(sport: Sport, member: MemberRowPerson): string {
  const admin = member.isOwner ? [GROUPS_COPY.members.admin] : [];
  return [memberName(member), ...admin, memberLine(sport, member)].join(', ');
}

/** *Open Zofia Bąk's record* — what a hold on the row does, named for the rotor. */
export function openRecordLabel(member: Pick<MemberRowPerson, 'name' | 'you'>): string {
  return member.you ? 'Open your record' : `Open ${personName(member.name)}’s record`;
}

/** *Let in · 2* — who a switch to Anyone admitted, on Edit group after the save. */
export function admittedEyebrow(count: number): string {
  return `Let in${DOT}${count}`;
}
