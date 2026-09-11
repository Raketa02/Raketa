/**
 * **The heartbeat** — *I am typing*, posted while the words are changing and never otherwise
 * ([ADR-0156](../../../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)
 * §2, [#404](https://github.com/Raketa02/Raketa/issues/404)).
 *
 * ## A beat per keystroke, throttled to the cadence, and nothing scheduled
 *
 * The composer calls {@link TypingHeartbeat.beat} from its own `onChangeText`, which fires only
 * on a keystroke — never on the words being put back after a refusal — and only while the field
 * has focus, so *while the field has focus and the text is changing* is met by the event rather
 * than by tracking either. `beatIsDue` (`domain/typing.ts`) is the throttle: the first keystroke
 * posts at once, and after that one post per cadence. **Nothing is scheduled**: a player who stops
 * typing stops beating, and the server's expiry is what clears the indicator on the far side.
 *
 * ## Not fire-and-forget, and not a mutation either
 *
 * *No fire-and-forget request in a component* is `query-and-errors.md`'s rule and the reason
 * this is a hook with an `AbortController` rather than a `void postTyping()` in the composer: a
 * beat in flight is aborted when the room unmounts, so no request outlives the screen that made
 * it, and the controller is the `signal` the rule asks to see passed through to `fetch`. It is
 * not a `useMutation`, because nothing about a heartbeat is a mutation the cache could hold — no
 * reply is written in, no error is drawn, and a paused one must not resume on reconnect to say
 * *typing* about a person who left the room a minute ago. `networkMode` has no honest value for
 * it, so it does not go through a machinery built around one.
 *
 * ## Silent when it fails, and silent when the account is held
 *
 * **A failed heartbeat is the one failure on this screen with no user-visible consequence worth
 * a word**: nobody needs to be told their typing indicator did not reach anybody. So a refusal is
 * caught and dropped, and a `401` has already gone through the app's own rotation before it could
 * get here. **A held account does not beat.** A hold stops you writing anywhere another player
 * sees it and an indicator is seen by other players, so `refused` closes this with the composer
 * — and the server would refuse it anyway, which is why the refusal is not read back: the room's
 * note is already up.
 */

import { useCallback, useEffect, useRef } from 'react';

import { beatIsDue } from '../domain/typing';
import { sayTyping } from '../use-cases/sayTyping';

export interface TypingHeartbeat {
  /** Say the words are changing. Throttled here; call it on every keystroke. */
  readonly beat: () => void;
}

export function useTypingHeartbeat(
  conversationId: string,
  { refused = false }: { readonly refused?: boolean } = {},
): TypingHeartbeat {
  /** When the last beat went out, on the device's monotonic clock. Not state: nothing draws it. */
  const lastBeatAt = useRef<number | undefined>(undefined);
  /** Aborts whatever is in flight when the room goes, so no beat outlives its screen. */
  const leaving = useRef(new AbortController());

  useEffect(() => {
    const controller = leaving.current;
    return () => controller.abort();
  }, []);

  const beat = useCallback(() => {
    if (refused) return;

    const now = Date.now();
    if (!beatIsDue(lastBeatAt.current, now)) return;
    lastBeatAt.current = now;

    // Silent by design — see the module note. Aborted on the way out, and an abort is a refusal
    // like any other from here.
    sayTyping({ conversationId, signal: leaving.current.signal }).catch(() => undefined);
  }, [conversationId, refused]);

  return { beat };
}
