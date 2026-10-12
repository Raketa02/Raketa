/**
 * **The notices while the app is open** — the banner, and a push tapped (#559; the screens A9: *an
 * in-app banner when the app is open*). `NoticesHost` draws what this answers; it is the shell's for
 * the session.
 *
 * ## The banner has two sources, and draws each notice once
 *
 * A9 gives the in-app banner a column of its own beside the push: a player who never allowed
 * notifications, or whose phone cannot be pushed yet — every phone, until Expo's project exists —
 * is still told while the app is open. So:
 *
 * - **A push arriving while the app is open** is the banner at once (`PushPort.onNotice`) — the
 *   phone draws nothing itself then.
 * - **The list behind the bell is read for the session** — on the way in, on every return to the
 *   app, whenever a push or an act marks it stale, and **every minute while this phone is not being
 *   pushed** (`usePushRegistration`'s answer). A notice the session has not seen before is the
 *   banner — the newest one, if a read brings several; the bell's number counts the rest.
 *
 * **What the session has seen is every id in its first read**, so a launch draws no banner for what
 * happened while the app was closed — the bell's number is the catch-up now (#627; Q101) — and a
 * pushed notice's id is seen the moment it is drawn, so the list's re-read after it does not draw it
 * twice. A notice the day bundled another into keeps its id and moves up the list: it is not new, and
 * nothing is drawn — the backend pushes nothing for it either. **A notice of the player's own act is
 * never the banner** (Q102): the yes that filled the game saw *It's a game!*, and the server pushes
 * no such notice either.
 *
 * **It re-reads, and changes nothing**: a push marks stale the list, Home's reads (the bar's badge
 * counts what needs the player, and every always-on notice moves it; *TO CONFIRM* above the games,
 * which a time to pay adds to and runs out on — `rereadHome`) and the read behind the screen it
 * opens — a push never changes what the server did not say (`docs/architecture.md` Part 13). **A
 * notice the list's read brings re-reads Home too** (Q103), so the game it is about is there before
 * it is tapped: without it the minute's read would leave Home as it was until the app had been away
 * for longer than Home stays fresh.
 *
 * ## A push tapped opens its game
 *
 * The phone's own notification, tapped with the app in the background or not running at all, opens
 * the game through `useOpenNotice`. The payload is checked first (`noticeOfPush`): one that is not a
 * notice's, or names what this build cannot, opens nothing.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';

import { rereadHome } from '@/features/proposals/types';
import { usePush } from '@/shared/lib/platform';

import { arrivalsOf, type NoticeTarget } from '../domain/notice';
import { noticeOfPush } from '../use-cases/notifications';

import { notificationKeys } from './notificationKeys';
import { rereadDestination, useOpenNotice } from './useOpenNotice';
import { usePushRegistration } from './usePushRegistration';
import { useRecentNotices } from './useRecentNotices';

/** How often the list is read while this phone is not being pushed — the banner's latency then. */
const WHILE_NOT_PUSHED = 60_000;

/** One notice drawn as the banner. */
export interface Banner {
  /** The notice's id — or, for a push this build could not read, the arrival's own. */
  readonly key: string;
  readonly title: string;
  readonly body: string;
  readonly target?: NoticeTarget;
}

let arrivals = 0;

export function useNotices(): {
  readonly banner: Banner | undefined;
  readonly close: () => void;
  readonly open: (target: NoticeTarget) => void;
} {
  const pushed = usePushRegistration();
  const push = usePush();
  const client = useQueryClient();
  const open = useOpenNotice();
  const [banner, setBanner] = useState<Banner | undefined>(undefined);
  /** Every notice id this session has seen — `undefined` until its first read of the list. */
  const seen = useRef<Set<string> | undefined>(undefined);

  const list = useRecentNotices({ every: pushed ? false : WHILE_NOT_PUSHED });

  useEffect(() => {
    const notices = list.data?.notices;
    if (notices === undefined) return;
    const known = seen.current;
    seen.current = new Set([...(known ?? []), ...notices.map((notice) => notice.id)]);
    if (known === undefined) return;
    const { arrived, banner: newest } = arrivalsOf(known, notices);
    if (arrived) void rereadHome(client);
    if (newest === undefined) return;
    setBanner({
      key: newest.id,
      title: newest.title,
      body: newest.body,
      ...(newest.target === undefined ? {} : { target: newest.target }),
    });
  }, [list.data, client]);

  useEffect(
    () =>
      push.onNotice((notice) => {
        const read = noticeOfPush(notice.data);
        if (read !== undefined) seen.current?.add(read.noticeId);
        void client.invalidateQueries({ queryKey: notificationKeys.notices() });
        void rereadHome(client);
        if (read?.target !== undefined) void rereadDestination(client, read.target);
        arrivals += 1;
        setBanner({
          key: read?.noticeId ?? `arrival-${arrivals}`,
          title: notice.title,
          body: notice.body,
          ...(read?.target === undefined ? {} : { target: read.target }),
        });
      }),
    [push, client],
  );

  const latestOpen = useRef(open);
  latestOpen.current = open;

  useEffect(
    () =>
      push.onOpen((data) => {
        const target = noticeOfPush(data)?.target;
        if (target !== undefined) latestOpen.current(target);
      }),
    [push],
  );

  const close = useCallback(() => setBanner(undefined), []);

  return { banner, close, open };
}
