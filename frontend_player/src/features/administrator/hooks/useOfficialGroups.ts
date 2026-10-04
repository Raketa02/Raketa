/**
 * **The Groups tab and one official group** — two reads, on the app's defaults.
 *
 * | | |
 * | --- | --- |
 * | `useAdministeredGroups` | `GET /administrator/clubs/{club}/groups` — the club, and the groups run there; a pull reads it again (`useAdministeredGroupsReread`) |
 * | `useOfficialGroup` | `GET …/groups/{id}` — one group: its link, players, requests and settings; a pull reads it again (`useOfficialGroupReread`) |
 *
 * Neither overrides anything: a group changes when somebody taps its link in WhatsApp, and the
 * thirty-second `staleTime` with a refetch on focus is what makes *N waiting* current when the
 * Administrator comes back to the app. The writes that change them say so in their own cache
 * effects (`useOfficialGroupWrites.ts`).
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AdministeredGroups, OfficialGroup } from '../domain/officialGroup';
import { readAdministeredGroups, readOfficialGroup } from '../use-cases/officialGroups';

import { administratorKeys } from './administratorKeys';

export function useAdministeredGroups(clubId: string) {
  return useQuery<AdministeredGroups, AppError>({
    queryKey: administratorKeys.groups(clubId),
    queryFn: ({ signal }) => readAdministeredGroups(clubId, { signal }),
  });
}

/**
 * **The Groups tab's pull** (#529) — the groups run at the club, read again now rather than marked
 * stale, so a request left or a player arrived since is on the cards when the spinner stops.
 */
export function useAdministeredGroupsReread(clubId: string): () => Promise<void> {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: administratorKeys.groups(clubId) });
}

/**
 * **An official group's page pull** (#529) — the group read again now, its requests and members
 * with it, so somebody who asked or arrived since is on the page when the spinner stops.
 */
export function useOfficialGroupReread(clubId: string, groupId: string): () => Promise<void> {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: administratorKeys.group(clubId, groupId) });
}

export function useOfficialGroup(clubId: string, groupId: string) {
  return useQuery<OfficialGroup, AppError>({
    queryKey: administratorKeys.group(clubId, groupId),
    queryFn: ({ signal }) => readOfficialGroup(clubId, groupId, { signal }),
  });
}
