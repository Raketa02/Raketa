/**
 * The two controls, wired: *Turn on* fires the OS prompt, *Not now* is not here.
 *
 * **The declining control has no hook and needs none.** It navigates or it
 * dismisses, and it touches nothing else — no request, no store, no record of
 * the answer. Giving it a function here would be inviting one.
 *
 * This is also the one place the real adapter meets the port a use-case
 * declares. `osNotifications` is checked against `PermissionAsker` **here**, so a
 * fourth `TimeSensitiveSetting` on the wire, a third platform, or a renamed
 * method fails `pnpm typecheck` at one site rather than in six.
 *
 * **A failure is swallowed, and stays swallowed.** Three things can go wrong —
 * the dialog, reading a token, the `PUT` — and none of them is hers. `ADR-0061`
 * is explicit that refusing costs a player the message and never the card, so a
 * *failure* must cost her no more than a refusal does: the screen moves on, and
 * the next launch's registration is what tries again. There is nothing to say
 * and no line to say it on.
 */

import { useCallback, useRef, useState } from 'react';

import { osNotifications } from '@/shared/lib/notifications';

import { askForNotifications, type PermissionAsker } from '../use-cases/askForNotifications';

/** The adapter, checked against what the workflow says it needs. */
const OS: PermissionAsker = osNotifications;

export interface NotificationAsk {
  /** The prompt is up, or the registration behind it is still in flight. */
  readonly asking: boolean;
  /** Resolves when the dialog has closed and anything behind it has finished. */
  readonly turnOn: () => Promise<void>;
}

export function useNotificationAsk(): NotificationAsk {
  const [asking, setAsking] = useState(false);
  // The prompt is spent once per install, so a second press while the first is
  // open must not reach the OS again. `busy` on the button covers the ordinary
  // case; this covers a caller that forgot to pass it.
  const inFlight = useRef(false);

  const turnOn = useCallback(async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setAsking(true);
    try {
      await askForNotifications(OS);
    } catch {
      // Deliberately nothing. See the note above.
    } finally {
      inFlight.current = false;
      setAsking(false);
    }
  }, []);

  return { asking, turnOn };
}
