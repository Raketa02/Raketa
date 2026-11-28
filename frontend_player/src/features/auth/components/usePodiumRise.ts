/**
 * **Sign-up's podium rising** — played once when the screen opens, and then still
 * ([#788](https://github.com/Rakieta02/Rakieta/issues/788), PRD #783; design system 12.2).
 *
 * ## Once, because it is a statement
 *
 * Sign-in's hero loops because it tells a story — a card dealt, picked up, swiped, a game made —
 * that is worth seeing again while somebody types. Sign-up's says one thing: **you, first**. Said
 * once it is a statement; said again every few seconds beside a form it would be a gesture, and the
 * eye would be pulled up off the password box to watch the same sentence. So it plays once, about a
 * second and a half, and the podium holds. **It plays again each time sign-up is opened again**:
 * *Sign in* goes back (`dismissTo`), which unmounts sign-up, and the next *Create an account* mounts
 * a new one, which rises.
 *
 * ## The beats
 *
 * All `motion.stagePodium`'s, in one `Animated.parallel` of three sequences, one per place, in
 * `RISING_ORDER` and `stagger` apart: after the `empty` stage, a step grows up to its height and its
 * player lands on it as it settles — the third and `ines.d`, the second and `stas.w`, then the volt
 * first and You. Six values, nought to one, and the podium draws from them: nothing re-renders as it
 * rises, so the form beside it never moves with it.
 *
 * ## Collapsed presentation
 *
 * Reduced motion, or a screen reader running: it never plays, and the podium stands risen with its
 * players. From the first frame when the rule is already known; a screen reader's answer is a
 * promise, and when it lands the rise is stopped and everything put where it ends. **Nothing replays
 * when the rule goes away** — the values are already at one, so a rise started then moves nothing.
 *
 * It does not follow `inView`: nothing is ever pushed over sign-up, and a rise that waited for the
 * screen it is drawn on would wait for nothing. A drawing's driver, so it lives beside the drawing
 * (`StagePodium`), as `useStageLoop` does.
 */

import { useEffect, useState } from 'react';
import { Animated } from 'react-native';

import { theme, useCollapsedPresentation } from '@/shared/ui';

import { ARRIVE, move } from './stageMotion';
import { PODIUM_PLACES, RISING_ORDER, type PodiumPlace } from './stagePodiumGeometry';

/** One place's two values, nought to one. */
export interface PodiumRise {
  /** Nought flat against the baseline, one at its height. */
  readonly step: Animated.Value;
  /** Nought not there, one landed on the step. */
  readonly player: Animated.Value;
}

/** The whole podium's — each place's step and player. */
export type StagePodiumMotion = Readonly<Record<PodiumPlace, PodiumRise>>;

const BEAT = theme.motion.stagePodium;

/** Every value at `at` — nought for the empty stage, one for the podium risen. */
function podiumAt(at: number): StagePodiumMotion {
  const place = (): PodiumRise => ({
    step: new Animated.Value(at),
    player: new Animated.Value(at),
  });
  return { first: place(), second: place(), third: place() };
}

/** The rise — see the module note. */
function rise(podium: StagePodiumMotion) {
  return Animated.parallel(
    RISING_ORDER.map((place, nth) =>
      Animated.sequence([
        Animated.delay(BEAT.empty + nth * BEAT.stagger),
        move(podium[place].step, 1, BEAT.step, ARRIVE),
        move(podium[place].player, 1, BEAT.player, ARRIVE),
      ]),
    ),
  );
}

export function usePodiumRise(): StagePodiumMotion {
  const collapsed = useCollapsedPresentation();
  // Risen from the first frame when the rule is already known — see the module note.
  const [podium] = useState(() => podiumAt(collapsed ? 1 : 0));

  useEffect(() => {
    if (collapsed) {
      for (const place of PODIUM_PLACES) {
        podium[place].step.setValue(1);
        podium[place].player.setValue(1);
      }
      return undefined;
    }

    const rising = rise(podium);
    rising.start();
    return () => rising.stop();
  }, [collapsed, podium]);

  return podium;
}
