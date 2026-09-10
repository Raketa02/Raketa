/**
 * The Android back button, claimed by the screen that has an answer for it.
 *
 * ## Why a screen has to claim it at all
 *
 * Android's back is a **navigator** gesture: unclaimed, React Navigation pops the stack, and
 * where there is nothing to pop the activity finishes. That is the right default for a stack
 * a player built by pushing, and the wrong one for every flow this app moves through with
 * `replace` — onboarding is the whole of that. A part walked with `replace` has one entry, so
 * the thing under it is whatever was on screen *before the part began*, and the system back
 * lands there: out of the part, past its own back control, and — since nothing is written
 * until the part commits — with the walk to do again
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md): *"Back and
 * forward move freely inside each part and never cross between them"*).
 *
 * So the rule is not *disable back*. It is:
 *
 * > **The device's back is the screen's own back control.** Where the screen draws one, the
 * > two do the same thing; where it draws none, the press is claimed and nothing happens.
 *
 * A press that does nothing is the honest answer on a first step, and it is what the *absence*
 * of a back control already says out loud — `stepBefore` and `questionNavigation`'s floor both
 * decline to offer one there, and a device gesture that walked out anyway would be a second,
 * louder answer to a question the screen has already answered.
 *
 * ## Claiming, and what `true` means
 *
 * A handler returning `true` means *handled — stop*. Handlers run in reverse registration
 * order, so a screen's own runs before the navigator's, which is what lets a screen answer
 * first. Returning `false` falls through to the navigator and then to the platform, and that
 * is the behaviour this hook exists to prevent, so **it always returns `true`**: a screen that
 * has taken the press has taken it whether or not it had somewhere to go.
 *
 * ## Only while the screen is on top, and that is not a refinement
 *
 * A stack keeps the screens under the top one **mounted**, so a plain `useEffect`
 * subscription outlives being looked at: a run's question screen sitting under the result
 * would go on answering the device's back, and — because handlers run in reverse registration
 * order — it would answer *before* anything a later screen registered. The symptom is a back
 * press that quietly moves a screen nobody can see.
 *
 * So the subscription is a **focus** effect: made when the screen comes to the top, dropped
 * when it leaves. The top screen is the only one subscribed, so LIFO never has to arbitrate,
 * and a screen that declines to answer declines on its own behalf rather than on the behalf of
 * whatever happens to be underneath.
 *
 * ## iOS
 *
 * There is no hardware back, and `BackHandler` on iOS registers a listener nothing ever
 * fires. Nothing is branched on the platform here: a no-op subscription is cheaper than a
 * conditional every caller would have to be right about, and the swipe-back gesture is the
 * navigator's own — a screen that wants it refused refuses it with `gestureEnabled`.
 */

import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef } from 'react';
import { BackHandler } from 'react-native';

/**
 * Answer the device's back button for as long as this component is mounted.
 *
 * Answered only while this screen is the one on top — see the module note.
 *
 * @param answer what the press does. Called on every press; **the press is always claimed**,
 *   so an `answer` that does nothing is how a screen refuses to be left. Read through a ref,
 *   so one subscription calls what the screen means now rather than the closure it was made
 *   with — `useOnForeground`'s rule, for its reason, and here it is also what keeps the
 *   subscription off the caller's dependency list: a screen whose answer is written inline
 *   would otherwise resubscribe on every render.
 */
export function useHardwareBack(answer: () => void): void {
  const latest = useRef(answer);

  useEffect(() => {
    latest.current = answer;
  }, [answer]);

  useFocusEffect(
    useCallback(() => {
      const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
        latest.current();
        return true;
      });

      return () => subscription.remove();
    }, []),
  );
}
