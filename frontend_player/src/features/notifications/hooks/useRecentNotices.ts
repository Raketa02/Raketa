/**
 * **The list behind the bell** — `GET /players/me/notices`, newest first (#559; the screens A9).
 *
 * The app's defaults — thirty seconds fresh, read again on focus — and **held for the session**
 * by `useNotices`, which re-reads it whenever a push arrives and every minute while the phone is not
 * pushed: it is the banner's second source, and the list the banner points at already holds the
 * notice it announced. Nothing marks a notice seen: the backend keeps no such thing.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Notice } from '../domain/notice';
import { readNotices } from '../use-cases/notifications';

import { notificationKeys } from './notificationKeys';

export function useRecentNotices({
  every = false,
}: {
  /** Read again every this many milliseconds — the session's read, while the phone is not pushed. */
  readonly every?: number | false;
} = {}) {
  return useQuery<readonly Notice[], AppError>({
    queryKey: notificationKeys.notices(),
    queryFn: ({ signal }) => readNotices({ signal }),
    refetchInterval: every,
  });
}
