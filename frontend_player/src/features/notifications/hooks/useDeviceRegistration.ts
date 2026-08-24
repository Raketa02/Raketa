/**
 * Re-state where this phone is, once per app session, for a player who has
 * already said yes.
 *
 * **Registering only on the tap would make the reported setting a lie within a
 * day.** `ADR-0065` reports `timeSensitiveSetting` for one reason — *"if a large
 * fraction of players revoke, this record's central judgement was wrong, and
 * reporting the setting is the only way we would ever learn it"* — and
 * revocation happens **after** a grant, in the OS settings app. A value captured
 * once at the moment she said yes would report that every player still has Time
 * Sensitive on, for ever, which is worse than no signal because it looks like
 * one.
 *
 * The same argument covers the token, which rotates on its own schedule: a
 * client that registered once would go quiet on the first rotation and nothing
 * anywhere would notice.
 *
 * **Once per session and not once per foreground**, which is the narrowing this
 * takes knowingly. A revocation between two foregrounds of one session is
 * reported at the next launch. The alternative is a request every time the app
 * comes back — on a screen (`ADR-0054`) whose whole design is that nothing
 * happens unless it is asked.
 *
 * **It holds no state and renders nothing.** No `useMutation`, no error, no
 * retry: nothing on any screen depends on the outcome, and a hook that set state
 * here would make every signed-in screen re-render for a fact no screen shows.
 */

import { useEffect, useRef } from 'react';

import { osNotifications } from '@/shared/lib/notifications';

import { registerDevice, type DeviceReader } from '../use-cases/registerDevice';

/** The adapter, checked against what the workflow says it needs. */
const OS: DeviceReader & { readonly standing: typeof osNotifications.standing } = osNotifications;

/**
 * @param enabled whether this player is in the app — the authenticated tree's own
 * answer, so a registration is never attempted for somebody the request would be
 * made unauthenticated for.
 */
export function useDeviceRegistration(enabled: boolean): void {
  const done = useRef(false);

  useEffect(() => {
    if (!enabled || done.current) return;
    done.current = true;

    void (async () => {
      // Nothing is asked, ever, from here: this is the *already granted* path,
      // and the one prompt belongs to a control she pressed (`ADR-0061`).
      if ((await OS.standing()) !== 'granted') return;
      await registerDevice(OS);
    })().catch(() => {
      // Deliberately nothing. There is no screen this could appear on.
    });
  }, [enabled]);
}
