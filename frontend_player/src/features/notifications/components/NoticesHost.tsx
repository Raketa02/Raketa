/**
 * **The notices, under the tabs** — what the shell mounts beside the signed-in app's screens for the
 * session (#559; the screens A9), as it holds the fill: the phone registered, a push tapped opened,
 * and the in-app banner — everything here outlives the screen the player is on. Which notice is the
 * banner, and when, is `useNotices`'.
 *
 * It provides nothing to the screens, so it wraps none of them: the shell places it after the bar,
 * and the banner is a layer over both. A banner is spoken once as it arrives, queued, and held for
 * `motion.hold.notice` — or until it is pressed or closed; the next notice replaces it, and holds for
 * its own time.
 */

import { useEffect } from 'react';

import { announce, theme } from '@/shared/ui';

import { useNotices } from '../hooks/useNotices';

import { NoticeBanner } from './NoticeBanner';
import { noticeSpoken } from './notificationsCopy';

export function NoticesHost() {
  const { banner, close, open } = useNotices();

  useEffect(() => {
    if (banner === undefined) return;
    announce(noticeSpoken(banner.title, banner.body));
    const held = setTimeout(close, theme.motion.hold.notice);
    return () => clearTimeout(held);
  }, [banner, close]);

  if (banner === undefined) return null;
  const target = banner.target;

  return (
    <NoticeBanner
      key={banner.key}
      title={banner.title}
      body={banner.body}
      onClose={close}
      {...(target === undefined
        ? {}
        : {
            onOpen: () => {
              close();
              open(target);
            },
          })}
    />
  );
}
