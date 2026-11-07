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
 *
 * **It also draws the record a notice opened** (#753): *You're friends* lands on the new friend's
 * record, which is `player_record`'s sheet rather than a screen, so it is drawn here — over whatever
 * the player is on, from the list, the banner or a push — for as long as the tabs are up. Closing it
 * forgets whose it was (`recordOpened.store`).
 */

import { useEffect } from 'react';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { announce, theme } from '@/shared/ui';

import { useNotices } from '../hooks/useNotices';
import { useRecordOpened } from '../store/recordOpened.store';

import { NoticeBanner } from './NoticeBanner';
import { noticeSpoken } from './notificationsCopy';
import { OPEN_NOTICE_WORDS } from './openNoticeWords';

export function NoticesHost() {
  return (
    <>
      <Banner />
      <OpenedRecord />
    </>
  );
}

/** The record a notice opened, if one did. */
function OpenedRecord() {
  const playerId = useRecordOpened((state) => state.playerId);
  const close = useRecordOpened((state) => state.close);
  if (playerId === undefined) return null;
  return (
    <PlayerRecordSheet
      key={playerId}
      visible
      onClose={close}
      subject={{ kind: 'player', playerId }}
    />
  );
}

function Banner() {
  const { banner, close, open } = useNotices(OPEN_NOTICE_WORDS);

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
