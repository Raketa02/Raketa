/**
 * **The Groups tab and one official group** — two reads, on the app's defaults.
 *
 * | | |
 * | --- | --- |
 * | `useAdministeredGroups` | `GET /administrator/clubs/{club}/groups` — the club, and the groups run there |
 * | `useOfficialGroup` | `GET …/groups/{id}` — one group: its link, players, requests and settings |
 *
 * Neither overrides anything: a group changes when somebody taps its link in WhatsApp, and the
 * thirty-second `staleTime` with a refetch on focus is what makes *N waiting* current when the
 * Administrator comes back to the app. The writes that change them say so in their own cache
 * effects (`useOfficialGroupWrites.ts`).
 */

import { useQuery } from '@tanstack/react-query';

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

export function useOfficialGroup(clubId: string, groupId: string) {
  return useQuery<OfficialGroup, AppError>({
    queryKey: administratorKeys.group(clubId, groupId),
    queryFn: ({ signal }) => readOfficialGroup(clubId, groupId, { signal }),
  });
}
