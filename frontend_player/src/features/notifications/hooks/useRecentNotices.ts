/**
 * **The list behind the bell, and the bell's number** — `GET /players/me/notices`, newest first
 * (#559; the screens A9), with the count of notices since the player last opened it (#627; Q101).
 *
 * The app's defaults — thirty seconds fresh, read again on focus — and **held for the session**
 * by `useNotices`, which re-reads it whenever a push arrives and every minute while the phone is not
 * pushed: it is the banner's second source, the bell draws its number from it, and the list the
 * banner points at already holds the notice it announced. What counts as seen is the server's,
 * moved by the visit the open list records (`useNoticesVisit`).
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { useReadFinished } from '@/shared/lib/query-client';

import type { RecentNotices } from '../domain/notice';
import { readNotices } from '../use-cases/notifications';

import { notificationKeys } from './notificationKeys';

export function useRecentNotices({
  every = false,
  opening = false,
}: {
  /** Read again every this many milliseconds — the session's read, while the phone is not pushed. */
  readonly every?: number | false;
  /**
   * Read again as this mounts, however fresh — the list being opened, whose visit must follow a
   * read of what it draws rather than one from before it was opened.
   */
  readonly opening?: boolean;
} = {}) {
  return useQuery<RecentNotices, AppError>({
    queryKey: notificationKeys.notices(),
    queryFn: ({ signal }) => readNotices({ signal }),
    refetchInterval: every,
    ...(opening ? { refetchOnMount: 'always' as const } : {}),
  });
}

/**
 * **Whether the bell's read has finished** (#871) — landed, refused, held for a connection, or failed
 * once and retrying: what the bell's number waits on before Home reveals it with the rest of your
 * things. Read off the cache, so it draws again only as it turns.
 */
export function useNoticesFinished(): boolean {
  return useReadFinished(notificationKeys.notices());
}
