/**
 * **The list behind the bell, opened** — the visit it records and the rows that stand out on it
 * ([#627](https://github.com/Raketa02/Raketa/issues/627); the mechanics Q101; the screens A9).
 *
 * ## The visit follows a read of what the list draws
 *
 * Opening the list reads it again however fresh it is, and **once that read lands the visit is
 * sent** (`POST /players/me/notices/visit`): whatever is listed by the time it arrives counts as
 * seen, so the bell is nought on every phone. A read that fails sends nothing — the bell keeps its
 * number, and the next opening tries again — and so does leaving before the read lands. While the
 * list stays open, **a read that brings a new row no visit has covered sends it again** — a notice
 * that reaches the open list, or one the day bundled into a row already there — so it is seen there
 * and not counted on the way back. When is the domain's (`readOnTheOpenList`).
 *
 * **Never held for later** (`networkMode: 'always'`): a visit sent on a reconnect the player never
 * saw would mark seen what reached the list while they were away. Not retried, for the same reason.
 * Once it lands, the list is written as the server will now answer it — nothing new, the number
 * nought — and read again, so Home's bell is clear the moment the player is back.
 *
 * ## The rows that stand out are held for the visit
 *
 * Every row a read while the list is open says is new — the cached read it opens on, the read the
 * visit follows, one that arrives while it is open — **stands out until the list is closed**, though
 * the server says none is new once the visit is recorded. The next opening starts from nothing.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';

import type { AppError } from '@/shared/errors';

import {
  JUST_OPENED,
  afterTheVisit,
  readOnTheOpenList,
  type RecentNotices,
} from '../domain/notice';
import { recordVisit } from '../use-cases/notifications';

import { notificationKeys } from './notificationKeys';
import { useRecentNotices } from './useRecentNotices';

export function useNoticesVisit() {
  const client = useQueryClient();
  const read = useRecentNotices({ opening: true });

  const { mutate: visit } = useMutation<void, AppError>({
    mutationFn: recordVisit,
    networkMode: 'always',
    onSuccess: () => {
      client.setQueryData<RecentNotices>(notificationKeys.notices(), (held) =>
        held === undefined ? held : afterTheVisit(held),
      );
      void client.invalidateQueries({ queryKey: notificationKeys.notices() });
    },
  });

  /** The open list between reads — read and written in one effect, so it is not render state. */
  const open = useRef(JUST_OPENED);
  const [standOut, setStandOut] = useState(JUST_OPENED.standOut);

  const data = read.data;
  // A read since the list opened that landed — not the cached one it opens on, and not a failure.
  const sinceOpening = read.isFetchedAfterMount && read.isSuccess;

  useEffect(() => {
    if (data === undefined) return;
    const after = readOnTheOpenList(open.current, data.notices, { sinceOpening });
    open.current = after.list;
    setStandOut(after.list.standOut);
    if (after.visit) visit();
  }, [data, sinceOpening, visit]);

  return { read, standOut };
}
