/**
 * **Sign-in's hero loop** — the deal, the pick-up, the swipe, *It's a game!* and the reset, over and
 * over ([#786](https://github.com/Rakieta02/Rakieta/issues/786),
 * [#787](https://github.com/Rakieta02/Rakieta/issues/787), PRD #783; design system 12.2).
 *
 * ## One sequence, looped, and no React state
 *
 * Every beat is `motion.stageDeck`'s, in one `Animated.sequence` that `Animated.loop` runs again from
 * its top: the cards stacked, then dealt; a still moment; the front card picked up and swiped off;
 * the splash coming up with the yes screen's own entrance — its sides meeting over `yesEntrance.sides`,
 * its word rising after `wordAfter` — and holding; the cards **restacked under it**, so nobody sees
 * them jump; the splash fading over them; its tiles put back off the edges once it has gone. Five
 * values carry the whole picture, and the components draw from them: nothing re-renders as the loop
 * moves, so typing in the form beside it never moves with it, and nothing in it sets state a test
 * would have to wrap.
 *
 * ## When it runs
 *
 * **Only while sign-in is the screen in view and the app is in the foreground** — `inView` from the
 * route (`useScreenInView`), and `useAppInBackground`, which is `AppState`'s `background` alone: iOS's
 * `inactive` — Face ID behind the keychain's autofill among it — leaves the loop running, so filling
 * the form from the keychain never resets the picture beside it. When either goes the loop stops
 * where it is; when both are back it **starts again from the deal**: the five values
 * are put back — stacked, the front card in its place, no splash — and the sequence runs from the
 * top, so nobody comes back to the middle of a swipe. A **Sign in** press touches none of it: a
 * success leaves the screen, which stops it, and a refusal leaves it running.
 *
 * **Under collapsed presentation it never runs** — reduced motion, or a screen reader running: the
 * cards are dealt and still, and there is no splash to draw (`splash` is undefined). The deal's value
 * starts dealt when the rule is already known at the first render; a screen reader's answer is a
 * promise, and when it lands the loop is stopped and the cards put where they belong.
 *
 * `Animated` on the native driver, as the yes screen and the deck do; the delays between beats are
 * timers, and every move is the native driver's. **A drawing's driver, so it lives beside the
 * drawings** (`StageDeck`, `StageSplash`), as `YesEntrance` does — not in `hooks/`, which is the
 * feature's reads.
 */

import { useEffect, useRef } from 'react';
import { Animated } from 'react-native';

import { useAppInBackground } from '@/shared/lib/platform';
import { theme, useCollapsedPresentation } from '@/shared/ui';

import { ARRIVE, curve, move, put } from './stageMotion';

/** The splash's three values — how much of it shows, its sides meeting, its word risen. */
export interface StageSplashMotion {
  readonly shown: Animated.Value;
  readonly meet: Animated.Value;
  readonly rise: Animated.Value;
}

/** The deck's two values — the deal, and the front card's swipe. */
export interface StageDeckMotion {
  /** Nought stacked, one dealt. */
  readonly deal: Animated.Value;
  /** The front card: nought in its place, one picked up with the stamp on it, two gone. */
  readonly swipe: Animated.Value;
}

export interface StageLoop {
  readonly deck: StageDeckMotion;
  /** The splash — undefined under collapsed presentation, where it is never drawn. */
  readonly splash: StageSplashMotion | undefined;
}

const BEAT = theme.motion.stageDeck;
const ENTRANCE = theme.motion.yesEntrance;

/** `easeAccel` — a card thrown off: slow away, then faster; *it accelerates right*. */
const THROW = curve(theme.motion.easeAccel);

/** The splash is up once its word has landed: the yes screen's entrance, end to end. */
const ENTRANCE_ENDS = ENTRANCE.wordAfter + ENTRANCE.word;

/** One cycle, from the stack — see the module note. */
function cycle(deal: Animated.Value, swipe: Animated.Value, splash: StageSplashMotion) {
  return Animated.sequence([
    Animated.delay(BEAT.stacked),
    move(deal, 1, BEAT.deal, ARRIVE),
    Animated.delay(BEAT.still),
    move(swipe, 1, BEAT.pickUp, ARRIVE),
    move(swipe, 2, BEAT.swipe, THROW),
    Animated.parallel([
      move(splash.shown, 1, theme.motion.fade),
      move(splash.meet, 1, ENTRANCE.sides),
      Animated.sequence([Animated.delay(ENTRANCE.wordAfter), move(splash.rise, 1, ENTRANCE.word)]),
    ]),
    Animated.delay(BEAT.splash - ENTRANCE_ENDS),
    // Under the night, so the jump is nobody's to see.
    put(deal, 0),
    put(swipe, 0),
    move(splash.shown, 0, BEAT.reset),
    // Once it has gone, so its tiles do not slide away in view.
    put(splash.meet, 0),
    put(splash.rise, 0),
  ]);
}

export function useStageLoop(inView: boolean): StageLoop {
  const collapsed = useCollapsedPresentation();
  const inTheBackground = useAppInBackground();
  const running = inView && !inTheBackground && !collapsed;

  // Dealt from the first frame when the rule is already known — see the module note.
  const deal = useRef(new Animated.Value(collapsed ? 1 : 0)).current;
  const swipe = useRef(new Animated.Value(0)).current;
  const shown = useRef(new Animated.Value(0)).current;
  const meet = useRef(new Animated.Value(0)).current;
  const rise = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!running) {
      // Stopped where it was — unless it is never to run, and then the picture's end state.
      if (collapsed) {
        deal.setValue(1);
        swipe.setValue(0);
        shown.setValue(0);
      }
      return undefined;
    }

    // From the deal, always: stacked, the front card in its place, no splash.
    deal.setValue(0);
    swipe.setValue(0);
    shown.setValue(0);
    meet.setValue(0);
    rise.setValue(0);

    const loop = Animated.loop(cycle(deal, swipe, { shown, meet, rise }), {
      resetBeforeIteration: false,
    });
    loop.start();
    return () => loop.stop();
  }, [running, collapsed, deal, swipe, shown, meet, rise]);

  return { deck: { deal, swipe }, splash: collapsed ? undefined : { shown, meet, rise } };
}
