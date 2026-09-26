/**
 * This feature's query-key factory — **every key it uses, with every parameter that changes the
 * answer.**
 *
 * Everything sits under one root, then the club, because every read is one Administrator's at one
 * club and a person running two clubs' groups is two Administrators (ADR-0184 §1). The Groups tab's
 * list and one group's page are **siblings** under the club rather than one under the other, so
 * re-reading the list never re-reads every page with it. A sign-out's `queryClient.clear()` takes
 * all of it.
 */

export const administratorKeys = {
  all: ['administrator'] as const,
  /** Everything read about one club's official groups. */
  club: (clubId: string) => [...administratorKeys.all, clubId] as const,
  /** The Groups tab: the club, and the groups this Administrator runs there. */
  groups: (clubId: string) => [...administratorKeys.club(clubId), 'groups'] as const,
  /** One official group, as its page reads it — its players and its requests with it. */
  group: (clubId: string, groupId: string) =>
    [...administratorKeys.club(clubId), 'group', groupId] as const,
  /** **A mutation key**: a create — keyed so the removal watch knows it is this feature's. */
  create: (clubId: string) => [...administratorKeys.club(clubId), 'create'] as const,
  /** **A mutation key**: a settings save — keyed so the removal watch knows it is this feature's. */
  settings: (clubId: string, groupId: string) =>
    [...administratorKeys.group(clubId, groupId), 'settings'] as const,
  /** **A mutation key**: the answers to one group's requests, counted to re-read it once. */
  answers: (clubId: string, groupId: string) =>
    [...administratorKeys.group(clubId, groupId), 'answer'] as const,
};
