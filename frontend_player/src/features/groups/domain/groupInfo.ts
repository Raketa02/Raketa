/**
 * **Info's rules** — what its members row draws, which way out of the group it offers,
 * and whether Edit group has anything to save
 * ([#514](https://github.com/Rakieta02/Rakieta/issues/514), PRD #500 stories 71–79,
 * [ADR-0183](../../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
 * §7).
 *
 * Pure: the group and the reader are read elsewhere. Who owns the group and who has been in
 * longest are the server's; this file only reads what came.
 */

import type { Group, GroupDetails, GroupMember, GroupPerson } from './group';

/**
 * **The members row's faces, and its *+N*** (play 58–60). The faces are the group's
 * `memberFaces` — up to five of everybody but the reader — and `more` counts **the other members
 * not drawn**, `memberCount - 1 - faces`. With no face served the reader stands in: alone, that
 * is play 57's own face, and were the faces ever empty with others in the group, it is still a
 * face on the row and `more` counts everybody else. (A block once emptied them; since ADR-0193 §2
 * it hides nobody.)
 */
export interface MembersRow {
  readonly faces: readonly GroupPerson[];
  readonly more: number;
}

export function membersRow(
  group: Pick<Group, 'memberFaces' | 'memberCount'>,
  reader: GroupPerson | undefined,
): MembersRow {
  const more = Math.max(0, group.memberCount - 1 - group.memberFaces.length);
  if (group.memberFaces.length > 0) return { faces: group.memberFaces, more };
  return { faces: reader === undefined ? [] : [reader], more };
}

/**
 * **The reader's own face, off the read the page already holds** — every sport's first rated
 * carries it for a reader among them, which a reader alone always is. Otherwise their poster:
 * a face with no photograph, which is what the poster is drawn from.
 */
export function readerFace(
  group: Pick<Group, 'ratedBySport'>,
  readerId: string | undefined,
): GroupPerson | undefined {
  if (readerId === undefined) return undefined;
  const rostered = group.ratedBySport
    .flatMap((roster) => roster.firstRated)
    .find((person) => person.playerId === readerId);
  return rostered ?? { playerId: readerId, name: null };
}

/**
 * **The way out** (stories 77–79): *Delete the group* for an Owner who is its only member, and
 * *Leave the group* for everybody else — an Owner with other members included, who passes it to
 * whoever has been in longest. The server refuses the other one either way round
 * (`lone_owner_cannot_leave`, `group_has_other_members`), for a count that moved since the read.
 */
export type GroupExit = 'delete' | 'leave';

export function groupExit(group: Pick<Group, 'isOwner' | 'memberCount'>): GroupExit {
  return group.isOwner && group.memberCount === 1 ? 'delete' : 'leave';
}

/**
 * **The refusals that mean the member count moved** since the page was read — everybody else left
 * an Owner's group, or somebody joined it — so the other way out is the one that works now, and
 * the group is worth reading again.
 */
const COUNT_MOVED: ReadonlySet<string> = new Set([
  'lone_owner_cannot_leave',
  'group_has_other_members',
]);

export function countMoved(code: string | undefined): boolean {
  return code !== undefined && COUNT_MOVED.has(code);
}

/**
 * **Whether Edit group's form says what the group already says** — then there is nothing to
 * save, and *Save* reads *Saved*. The form's name is compared trimmed, as it is sent.
 */
export function detailsUnchanged(
  details: GroupDetails,
  group: Pick<Group, 'name' | 'joinPolicy'>,
): boolean {
  return details.name.trim() === group.name && details.joinPolicy === group.joinPolicy;
}

/**
 * **Who wears Members' admin tag** (play 61; #519): a player group's Owner, and an official group's
 * Administrator who joined it as a player — the one who answers its requests, either way. An
 * official group has no Owner, and the Administrator who has not joined is not on the list at all.
 */
export function adminTagged(member: Pick<GroupMember, 'isOwner' | 'isAdministrator'>): boolean {
  return member.isOwner || member.isAdministrator;
}

/**
 * **Who runs the group, where Members names them apart from its list** (#529, the product owner's
 * ask). A member can always find who runs the group they are in, to know who answers for it: a
 * player group's Owner is one of its members and leads the list with the **admin** tag, but an
 * official group's Administrator need not play in it, and was then on no list at all. So Members
 * names them over the list — their whole nickname, the admin tag and the club they run it for — and,
 * while the group **needs an administrator**, the club in their place, which holds the group until
 * it hands it on (ADR-0183 §3).
 *
 * **Nobody is drawn twice**, so nothing is drawn (`undefined`): on a player group; for a reader who
 * runs it, who is *You* wherever they play; and where the sport's list carries the Administrator's
 * own admin-tagged row, which says it better — their face, their Level, a tap to their record. A
 * sport they are not rated in names them over the list again.
 */
export type GroupRunner =
  | { readonly kind: 'administrator'; readonly name: string; readonly clubName: string }
  | { readonly kind: 'club'; readonly clubName: string };

export function runnerApart(
  group: Pick<Group, 'kind' | 'administratorName' | 'isAdministrator' | 'homeClub'>,
  members: readonly Pick<GroupMember, 'isAdministrator'>[],
): GroupRunner | undefined {
  if (group.kind !== 'OFFICIAL' || group.isAdministrator) return undefined;
  if (members.some((member) => member.isAdministrator)) return undefined;
  const clubName = group.homeClub.name;
  return group.administratorName === null
    ? { kind: 'club', clubName }
    : { kind: 'administrator', name: group.administratorName, clubName };
}
