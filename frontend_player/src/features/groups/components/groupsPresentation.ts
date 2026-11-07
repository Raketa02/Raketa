/**
 * **Every sentence Groups, New group, Join a group and the group page compose from a value** —
 * and every name a control is spoken by. The fixed sentences are `groupsCopy.ts`, re-exported
 * here; copy is code, and nothing is inlined in a component.
 *
 * Taken from the mocks (play 1, 3–17, 23–55), with the mocks' *Rakieta* read as **Raketa**
 * (ADR-0187 §8). Two rules sit over it:
 *
 * - **A nickname is said whole, never with an @.** The *approves joins* line carries the Owner's or
 *   the Administrator's whole nickname — the Administrator's club-typed name until they have one
 *   (ADR-0199 §4) — and the row truncates the line, as it truncates any line; nothing is cut from
 *   it here or on the server (ADR-0199 §1, #505, #519).
 * - **A counted phrase goes through `counted()`**, so *1 member* is never *1 members* and a market
 *   with real plural rules has one function to change.
 */

import { sportInLine, sportLabel, sportShortLabel } from '@/features/onboarding/types';
import { RELIABILITY_BAND_WORD } from '@/features/player_record/types';
import { counted } from '@/shared/formatting/counted';
import { linkWithoutScheme } from '@/shared/formatting/linkFormat';
import { playerName } from '@/shared/formatting/playerName';
import { formatDistanceKm, formatLevel } from '@/shared/formatting/ratingFormat';
import type { SeatPlace } from '@/shared/vocabulary/seatPlace';
import { courtSummaryLabel, seatLabel } from '@/shared/vocabulary/seatPlacePresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  GROUP_NAME_MAX,
  type Group,
  type GroupAtClub,
  type GroupMember,
  type SearchedClub,
  type SportLevel,
} from '../domain/group';
import { adminTagged, type GroupExit, type GroupRunner } from '../domain/groupInfo';
import type { GroupKind } from '../domain/vocabulary';
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

/** *8 members* */
export function membersLine(count: number): string {
  return counted(count, 'member', 'members');
}

/** *1 member · Bonarka Arena* — the group page's second line (play 40). */
export function membersAtClub(count: number, clubName: string): string {
  return `${membersLine(count)}${DOT}${clubName}`;
}

/**
 * **Whether joining needs somebody's yes** — *anyone can join* on an Anyone group, and *Needs
 * approval* on every other, whoever answers: a player group's Owner, an official group's
 * Administrator or its club, which answers at any time (#529, ADR-0191 §1). The row named them until the
 * owner asked for the shorter line; who answers is on the group's page once the reader is in.
 */
export function approverLine(group: Pick<GroupAtClub, 'joinPolicy'>): string {
  return group.joinPolicy === 'ANYONE'
    ? GROUPS_COPY.info.anyoneCanJoin
    : GROUPS_COPY.info.needsApproval;
}

/** *11 members · Needs approval* — a group row's second line (play 9, 35). */
export function groupRowMeta(group: GroupAtClub): string {
  return `${membersLine(group.memberCount)}${DOT}${approverLine(group)}`;
}

/** *Tennis, Padel* — a club's sports, in the order the club serves them. */
function sportsList(sports: SearchedClub['sports']): string {
  return sports.map(sportLabel).join(', ');
}

/**
 * *Grzegórzki · 2,4 km · Tennis, Padel* — a club's line under its name, wherever a club is drawn.
 *
 * The distance is **never drawn for a reader with no Location area**, whose clubs come A–Z with
 * `null` for a distance (story 28). Home-club search's rows draw it too since the 2026-09-27
 * mocks, which overrode #512's *no distance in these rows*.
 */
export function clubLine(club: SearchedClub): string {
  const parts = [club.district];
  if (club.distanceKm !== null) parts.push(formatDistanceKm(club.distanceKm));
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

/** A card on the Groups list, spoken: name, *official* where it is, size, sports and home club. */
export function groupCardLabel(group: {
  readonly kind: GroupKind;
  readonly name: string;
  readonly memberCount: number;
  readonly sports: SearchedClub['sports'];
  readonly homeClub: { readonly name: string };
}): string {
  // The mark beside an official group's name has no words of its own, so the card says it.
  const tagged = group.kind === 'OFFICIAL' ? [GROUPS_COPY.official] : [];
  const plays = group.sports.length > 0 ? [`plays ${sportsList(group.sports)}`] : [];
  return [
    group.name,
    ...tagged,
    membersLine(group.memberCount),
    ...plays,
    group.homeClub.name,
  ].join(', ');
}

/**
 * *Games, 4 with somebody In* — the group page's Games tab, spoken with its count: the cards where
 * somebody is already In with you (#553, the screens A1).
 */
export function gamesTabLabel(cards: number): string {
  return `${GROUPS_COPY.group.tabs.games}, ${cards} with somebody In`;
}

/** *Fill in, 1 seat to fill* — the Fill in tab, spoken with its count (#557). */
export function fillInTabLabel(seats: number): string {
  return `${GROUPS_COPY.group.tabs.fillIn}, ${counted(seats, 'seat', 'seats')} to fill`;
}

/**
 * A home-club search result's head, spoken — the whole head is the one tap. The groups drawn under
 * it are rows of their own and speak for themselves.
 */
export function setAsHomeLabel(club: SearchedClub): string {
  return `Set ${club.name} as home club, ${clubLine(club)}`;
}

/** A club's card header in Join a group, spoken — context, not a button (story 39). */
export function clubCardLabel(club: SearchedClub): string {
  return `${club.name}, ${clubLine(club)}`;
}

/** The chosen home club's card, spoken. */
export function chosenClubLabel(club: SearchedClub): string {
  return `Home club: ${club.name}, ${clubLine(club)}`;
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

/** *padel*, *padel and squash*, *padel, tennis or badminton* — sports inside a sentence. */
function sportsInLine(sports: readonly Sport[], conjunction: 'and' | 'or'): string {
  const words = sports.map(sportInLine);
  const last = words.at(-1) ?? '';
  return words.length <= 1 ? last : `${words.slice(0, -1).join(', ')} ${conjunction} ${last}`;
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
 * Friends court's summary and the Games card's row of seats alike. It is the court's own sentence
 * (`courtSummaryLabel`, the-words §20.4), so a group's court and a line-up's say the same thing.
 */
export function seatsFilledLabel(sport: Sport, filled: number, seats: number): string {
  return courtSummaryLabel({ sportName: sportLabel(sport), filled, seats });
}

/**
 * *Your side, you, level 2,71* — the reader's seat on the Friends court: the seat's own sentence,
 * and the Level the seat draws under the face, in the words a seat says a Level in.
 */
export function yourSeatLabel(place: SeatPlace, level: number | undefined): string {
  const seat = seatLabel(place, { kind: 'you' });
  return level === undefined ? seat : `${seat}, level ${formatLevel(level)}`;
}

/** *Their side, empty* — a seat a friend could fill, named by where it is (`seatLabel`). */
export function emptySeatLabel(place: SeatPlace): string {
  return seatLabel(place, { kind: 'empty' });
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
// Info, Members and Edit group (#514)
// ---------------------------------------------------------------------------

/**
 * *raketa.app/join/K7PQ2MXA* — the link as Info's card draws it (play 57, 60): the address
 * without its scheme, which the mocks never print. Spoken, copied and shared whole. The drawing is
 * `shared/formatting`'s since a friend link's card is its third caller (#756).
 */
export function linkShown(link: string): string {
  return linkWithoutScheme(link);
}

/** *Group link, raketa.app/join/K7PQ2MXA* — the card's link, spoken. */
export function linkLabel(link: string): string {
  return `Group link, ${linkShown(link)}`;
}

/**
 * *anyone can join*, *you approve joins*, *the owner approves joins* — the members row's policy
 * line. The group's read names no Owner, so a member who is not one reads *the owner*, as a row
 * whose Owner can no longer be named does. **An official group has no Owner** and its read names
 * no Administrator either, so it reads *the administrator approves joins* (#519).
 */
export function infoPolicyLine(group: Pick<Group, 'kind' | 'joinPolicy' | 'isOwner'>): string {
  if (group.joinPolicy === 'ANYONE') return GROUPS_COPY.info.anyoneCanJoin;
  switch (group.kind) {
    case 'PLAYER':
      return group.isOwner ? GROUPS_COPY.info.youApprove : GROUPS_COPY.info.ownerApproves;
    case 'OFFICIAL':
      return GROUPS_COPY.info.administratorApproves;
  }
}

/** *+2* — the members row's count of everybody it does not draw. */
export function moreFaces(count: number): string {
  return `+${count}`;
}

/** *8 members, plays Padel, Tennis, anyone can join* — the members row, spoken; it opens Members. */
export function membersRowLabel(
  group: Pick<Group, 'kind' | 'memberCount' | 'sports' | 'joinPolicy' | 'isOwner'>,
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

/** How many of a request's sports its row draws as tags; the rest are one *+N* tag. */
const REQUEST_TAGS_SHOWN = 2;

/** One sport a request's row draws: its dot's sport, and *Pad 2,44*. */
export interface RequestTag {
  readonly sport: Sport;
  readonly label: string;
}

/**
 * *Pad 2,44 · Ten 2,60 · +2* — what a request's row draws under the name (#529): **the first two
 * sports in the order served**, short, each with its Level, and one *+N* for the rest, so four
 * sports never run the row onto a second line. Drawn only — the row is spoken with
 * `requestLevels`, every sport by its whole name.
 */
export function requestTags(levels: readonly SportLevel[]): {
  readonly shown: readonly RequestTag[];
  readonly more?: string;
} {
  const shown = levels.slice(0, REQUEST_TAGS_SHOWN).map(({ sport, level }) => ({
    sport,
    label: `${sportShortLabel(sport)} ${formatLevel(level)}`,
  }));
  const rest = levels.length - shown.length;
  return rest > 0 ? { shown, more: `+${rest}` } : { shown };
}

/** A nickname as a row draws it — whole, or the word for somebody who can't be named. */
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

/**
 * **A group's header, spoken, where its drawn words are not the whole of it** — on its page and on
 * Info. An official group's mark has no words of its own, so the header says *official* (#529),
 * and the Owner's count of waiting requests on the tile is said after the line under the name
 * (Q125, the Info tab's count before it): *Ogrody 33 Club, official, 12 members · Ogrody 33, 2
 * requests waiting*. `undefined` where the name and the line are all there is, so the header is
 * named by its drawn words rather than labelled with them (`ScreenHeader`'s rule).
 */
export function groupHeaderLabel(
  group: Pick<Group, 'kind' | 'name' | 'memberCount' | 'homeClub'>,
  waiting = 0,
): string | undefined {
  const official = group.kind === 'OFFICIAL';
  if (!official && waiting === 0) return undefined;
  return [
    group.name,
    ...(official ? [GROUPS_COPY.official] : []),
    membersAtClub(group.memberCount, group.homeClub.name),
    ...(waiting > 0 ? [`${counted(waiting, 'request', 'requests')} waiting`] : []),
  ].join(', ');
}

/**
 * *Members · 8* — the screen's title, with how many here play the filter's sport: it moves with the
 * pill. The word alone before the list is in, and where there is no sport to list.
 */
export function membersTitle(count: number | undefined): string {
  return count === undefined
    ? GROUPS_COPY.members.title
    : `${GROUPS_COPY.members.title}${DOT}${count}`;
}

/**
 * *Padel 2,71* — a row's line, after the sport's dot. Player reliability left it for a tag beside
 * the name (`PlayerScoreTag`), so the line is the sport and its Level and nothing else.
 */
export function memberLine(sport: Sport, member: Pick<GroupMember, 'level'>): string {
  return `${sportLabel(sport)} ${formatLevel(member.level)}`;
}

/** Who a Members row is about, and whether it is the reader's own. */
export interface MemberRowPerson extends Pick<
  GroupMember,
  'name' | 'level' | 'playerScore' | 'reliabilityBand' | 'isOwner' | 'isAdministrator'
> {
  readonly you: boolean;
}

/** *You* for the reader's own row, the whole nickname for anybody else (play 61). */
export function memberName(member: Pick<MemberRowPerson, 'name' | 'you'>): string {
  return member.you ? playerName({ kind: 'you' }) : personName(member.name);
}

/**
 * *Karol Tomczak, reliability 75, High, admin, Padel 2,75* — a row, spoken in the order it is
 * drawn: the name, the score tag, the admin tag, the line (#660). **The tag's tint is said as the
 * band's word**: the band is the server's fact now rather than this phone's reading of the
 * figure, and colour is never its only carrier. A band this build cannot name is not said.
 */
export function memberRowLabel(sport: Sport, member: MemberRowPerson): string {
  const band =
    member.reliabilityBand === undefined ? [] : [RELIABILITY_BAND_WORD[member.reliabilityBand]];
  const admin = adminTagged(member) ? [GROUPS_COPY.members.admin] : [];
  return [
    memberName(member),
    `${GROUPS_COPY.members.reliability} ${member.playerScore}`,
    ...band,
    ...admin,
    memberLine(sport, member),
  ].join(', ');
}

/** *Opens their record* — what a tap on a row does. The row's label already says whose. */
export function openRecordHint(member: Pick<MemberRowPerson, 'you'>): string {
  return member.you ? GROUPS_COPY.members.openYours : GROUPS_COPY.members.openTheirs;
}

/** *Marta Wójcik* — who runs an official group, whole; the club's name while nobody does. */
export function runnerName(runner: GroupRunner): string {
  return runner.kind === 'administrator' ? runner.name : runner.clubName;
}

/**
 * *runs this group for Ogrody 33* — the line under who runs it, or that nobody does now: lower case,
 * as Info's *approves joins* line is drawn.
 */
export function runnerLine(runner: GroupRunner): string {
  return runner.kind === 'administrator'
    ? `runs this group for ${runner.clubName}`
    : GROUPS_COPY.members.noAdministrator;
}

/**
 * *Marta Wójcik, admin, runs this group for Ogrody 33* — who runs it, spoken in the order it is
 * drawn: the name, the admin tag, the line. *Ogrody 33, no administrator right now* while nobody
 * does, which draws no tag.
 */
export function runnerLabel(runner: GroupRunner): string {
  const admin = runner.kind === 'administrator' ? [GROUPS_COPY.members.admin] : [];
  return [runnerName(runner), ...admin, runnerLine(runner)].join(', ');
}

/**
 * **A club's two letters, for its tile** (club 5–7: *O3* for Ogrody 33) — the administrator area's
 * profile switcher, and Members' who-runs-it. A club is served no monogram of its own — a group's
 * letters are cut by the backend (ADR-0183 §5), a club's are not — so they are taken here: the
 * first character of each of the first two words, or the first two of a name that is one word.
 * Drawn as they come, never re-cased, as a group's are.
 */
export function clubLetters(clubName: string): string {
  const [first = '', second] = clubName.trim().split(/\s+/);
  const initial = (word: string) => [...word][0] ?? '';
  return second === undefined ? [...first].slice(0, 2).join('') : initial(first) + initial(second);
}

/** *Let in · 2* — who a switch to Anyone admitted, on Edit group after the save. */
export function admittedEyebrow(count: number): string {
  return `Let in${DOT}${count}`;
}

// ---------------------------------------------------------------------------
// An official group, for a player rated in none of its sports (#519)
// ---------------------------------------------------------------------------

/** *This group plays padel* — the card's headline (story 57), every sport the group declares. */
export function addSportHeadline(sports: readonly Sport[]): string {
  return `This group plays ${sportsInLine(sports, 'and')}`;
}

/** *Get rated in padel to post here* — *Post a game* for a reader rated in none of the sports (Q80). */
export function rateToPostHeadline(sports: readonly Sport[]): string {
  return `Get rated in ${sportsInLine(sports, 'or')} to post here`;
}

/** *Add padel to your Skill passport to see its games.* — any one of them will do. */
export function addSportLine(sports: readonly Sport[]): string {
  return `Add ${sportsInLine(sports, 'or')} to your Skill passport to see its games.`;
}

/**
 * *Rate Padel* — the door into the questionnaire for one of them, named as a control is, and as
 * the Skill passport's own chip names it (#729, ADR-0200 §3). It was *Add Padel* while the pass
 * ended on the passport.
 */
export function rateSportLabel(sport: Sport): string {
  return `Rate ${sportLabel(sport)}`;
}
