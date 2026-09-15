/**
 * The deck's stage: **a card under the thumb, two stamps over it, two real cards behind it**
 * — and the card arriving, settling back, or flying.
 *
 * ## A swipe is an answer, and the buttons remain the path
 *
 * [#231](https://github.com/Raketa02/Raketa/issues/231) §3 refused the gesture because *Show
 * them again* had been struck, which left a pass as a thirty-day act with nothing that reverses
 * one — a swipe would have put the cheapest gesture in the app on the most durable act in it.
 * [ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5 gave the pass its reset and §3 gave the deck its drag: right is *Let's play*, left is *Not
 * today*, the stamps fade in with the drag and are full at the threshold, past which a release
 * commits; short of it the card settles back. The three buttons below the stage do the same two
 * things and one more, and **they are never removed**: VoiceOver and TalkBack consume the drag,
 * so the buttons are the accessible path and the drag is never the only one (§20.5's other half).
 *
 * ## Built on the responder the app already drags with
 *
 * React Native's own `PanResponder` and `Animated` with the native driver — **no
 * `react-native-gesture-handler`, no `react-native-reanimated`** — because the chat row and the
 * radius slider prove the pattern. The stage **never claims the touch when it lands**: the card
 * under the finger is a door — a long press opens the record — and a tap and a hold have to
 * reach it. It claims on a *move*, once `deckStageGeometry` says the finger has travelled the
 * intent distance across and further across than down, in either direction; until then every
 * move is the page's. Once claimed, the page may not take the gesture back
 * (`onPanResponderTerminationRequest: false`), on the slider's own argument: a card that lost
 * the finger to a scroll would be left half off the stage.
 *
 * ## Where the card goes, and who decides
 *
 * Under the finger it tracks exactly — across, and a little down, because a card lifted by a
 * thumb moves with the thumb — and turns by `tilt()`. On release the stage asks the screen:
 * `onAnswer(said)` returns **`taken`** and the screen sets `leaving`, on which the card flies
 * in the answer's direction from wherever the finger left it; or **`withheld`** — the ceiling,
 * with no yeses to give (`domain/yesBudget`) — and the card settles back with nothing sent. A
 * button press sets `leaving` from rest and the same flight runs from nought. The direction is
 * the whole of what the answer changes: the travel, the turn, the fade and the duration are one
 * pair of animations mirrored, held as a **sign**, so the one mid-flight when a refusal returns
 * the card is the one reset to nought.
 *
 * ## One haptic, at the threshold, and none under reduced motion
 *
 * The motor ticks once as the finger **first** crosses the threshold in a gesture, so a thumb
 * knows the release will commit without looking at the stamp — `expo-haptics`' light impact,
 * through the port ADR-0167 already added. Under collapsed presentation there is no motion and
 * no buzz, and the answer still lands: `onLeft` is a **fact** rather than an animation's
 * courtesy, and a callback that only fired when the animation ran would leave a listener holding
 * a deck that never advances.
 *
 * ## Two real cards behind, and the stack is the stage's height
 *
 * The cards behind are the hand's next two people drawn as real cards, offset down and scaled
 * back, and only when that many remain — never a placeholder (§3). They are absolutely laid
 * over the stage and the stage takes `flex: 1`, so all three cards are one size: the height the
 * phone gives the deck, not the height a card's own content happens to want. They are hidden
 * from assistive technology, because the top card is the one element and a listener does not
 * hear the queue.
 *
 * ## The durations live here rather than in the theme
 *
 * `theme.motion` is *"one entrance, one sheet, one popover, one fade"* and holds the shared
 * floors beside them; the engine fill's per-seat stagger is deliberately not there because *"it
 * is the court's own and belongs beside the animation it drives"*. The flight is the same case
 * — one surface, one pair of animations, numbers that mean nothing anywhere else — and the
 * settle borrows `motion.settle`, because a card coming to rest under a lifted finger is the
 * swipe row's own beat. The arrival borrows `motion.rise`: a card appearing is the entrance
 * every other surface already uses, and here it rises from the place the card behind it stood.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { Animated, PanResponder, StyleSheet, Text, View } from 'react-native';

import { useHaptics } from '@/shared/lib/platform';
import { theme, useCollapsedPresentation } from '@/shared/ui';

import { STAMP_WORDS } from './deckPresentation';
import {
  claimsTheDrag,
  committed,
  crossedThreshold,
  stampOpacity,
  tilt,
  wayOf,
  type DeckExit,
} from './deckStageGeometry';

export type { DeckExit } from './deckStageGeometry';

/**
 * How long a card takes to leave — the prototype's `cardout`, kept.
 *
 * Shorter than the arrival on purpose: the answer has already been given, and the only thing
 * this beat buys is seeing that it landed. Long enough to read as *that one is gone*, short
 * enough that a player answering ten cards is not waiting on it nine times.
 */
const LEAVING_MS = 240;

/**
 * How much of the finger's travel **down** the card follows — a thumb drags a card across, and
 * the card lifts a little with it; all of it would make a horizontal gesture wander.
 */
const LIFT_SHARE = 0.3;

/**
 * The stack behind the top card: each card behind sits one `step` lower and `shrink` smaller
 * than the one in front, and the top card **arrives** from the first step — the place the card
 * behind it stood — so a card advancing reads as the same object coming forward.
 */
const STACK = { step: theme.space.sm, shrink: 0.05 } as const;

/**
 * The stamps' own drawing: a 3pt outline, a 12° tilt away from the card's centre, inset a large
 * step from the card's edge, and **90pt down** — under the Level's block, where the two swipe
 * mocks put them and clear of the mark either way. The drawing's own numbers, as the yes
 * ground's glow keeps its centre and reach; the words and the type role are the theme's.
 */
const STAMP = { stroke: 3, tilt: 12, inset: theme.space.xl, top: 90 } as const;

/** What the screen answers when a drag commits — whether the card may fly. */
export type DragVerdict = 'taken' | 'withheld';

export interface DeckStageProps {
  /**
   * The answer this card was given and is leaving on, or `undefined` while it is still being
   * decided.
   *
   * The screen owns it, because *which card is showing* is derived from the deal minus the one
   * leaving, and is deliberately held nowhere else (`playSession`).
   */
  readonly leaving: DeckExit | undefined;
  /**
   * A drag released past the threshold. The screen answers whether it took the answer — on
   * `taken` it sets `leaving` and the card flies; on `withheld` the card settles back.
   */
  readonly onAnswer: (said: DeckExit) => DragVerdict;
  /**
   * The card has gone. Called once, whether it travelled or not.
   *
   * This unlocks the buttons and advances the deck, so it is a **fact** rather than an
   * animation's courtesy.
   */
  readonly onLeft: () => void;
  /** The top card. */
  readonly children: ReactNode;
  /** The cards behind, nearest first — real cards or nothing, never placeholders. */
  readonly behind?: readonly ReactNode[];
}

export function DeckStage({ leaving, onAnswer, onLeft, children, behind = [] }: DeckStageProps) {
  const collapsed = useCollapsedPresentation();
  const haptics = useHaptics();
  // One value per phase, and each drives every transform in it: a card is one object moving,
  // where four values would be four things able to be halfway through different animations.
  // `drag` is where the finger has put the card, and the flight continues from there.
  const drag = useRef(new Animated.ValueXY()).current;
  const arrival = useRef(new Animated.Value(0)).current;
  // Refs rather than dependencies: the pan handlers are created once and must not close over a
  // render's values, and the handlers close over the card that was answered — re-running the
  // flight because a parent re-rendered would restart a card mid-exit.
  const now = useRef({ leaving, collapsed, onAnswer, onLeft, haptics });
  now.current = { leaving, collapsed, onAnswer, onLeft, haptics };
  /** Whether the motor has ticked in this gesture — once per gesture, on the first crossing. */
  const ticked = useRef(false);

  const settle = useRef(() => {
    if (now.current.collapsed) {
      drag.setValue({ x: 0, y: 0 });
      return;
    }
    Animated.timing(drag, {
      toValue: { x: 0, y: 0 },
      duration: theme.motion.settle,
      useNativeDriver: true,
    }).start();
  }).current;

  const responder = useRef(
    PanResponder.create({
      // Never on the press itself: the card is a door, and a tap and a long press reach it.
      onMoveShouldSetPanResponder: (_event, gesture) =>
        now.current.leaving === undefined && claimsTheDrag(gesture),
      // The page may not take the gesture back mid-drag — the slider's own rule.
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        ticked.current = false;
      },
      onPanResponderMove: (_event, gesture) => {
        drag.setValue({ x: gesture.dx, y: gesture.dy * LIFT_SHARE });
        if (!ticked.current && crossedThreshold(gesture.dx)) {
          ticked.current = true;
          if (!now.current.collapsed) now.current.haptics.light();
        }
      },
      onPanResponderRelease: (_event, gesture) => {
        const said = committed(gesture.dx);
        if (said === undefined || now.current.onAnswer(said) === 'withheld') settle();
        // Taken: the screen sets `leaving`, and the flight runs from where the finger left it.
      },
      // The system took the touch — a call, a notification. The card still has to land.
      onPanResponderTerminate: () => settle(),
    }),
  ).current;

  useEffect(() => {
    if (collapsed) {
      arrival.setValue(1);
      return;
    }

    const rise = Animated.timing(arrival, {
      toValue: 1,
      duration: theme.motion.rise,
      useNativeDriver: true,
    });
    rise.start();
    return () => rise.stop();
  }, [collapsed, arrival]);

  useEffect(() => {
    if (leaving === undefined) {
      // **A card that comes back comes back straight.** An answer refused puts the card on
      // screen again, and a stopped `Animated.Value` keeps whatever fraction of the flight it
      // reached — so without this the returned card sits shifted and turned, mid-exit, on the
      // one path the screen documents as recoverable.
      drag.setValue({ x: 0, y: 0 });
      return;
    }

    if (collapsed) {
      now.current.onLeft();
      return;
    }

    const flight = Animated.timing(drag.x, {
      toValue: wayOf(leaving) * theme.size.deckSwipe.flight,
      duration: LEAVING_MS,
      useNativeDriver: true,
    });
    flight.start(({ finished }) => {
      if (finished) now.current.onLeft();
    });

    // Unmounted mid-flight — the deal was replaced, or the tab was left. Stopping is what
    // keeps the callback from firing into a screen that is no longer there.
    return () => flight.stop();
  }, [leaving, collapsed, drag]);

  return (
    <View style={s.stage}>
      {/* Deepest first, so the nearer card paints over the further one and the top card over
          both. Hidden from assistive technology: the top card is the one element. */}
      {[...behind].reverse().map((card, fromTheBack) => {
        const depth = behind.length - fromTheBack;
        return (
          <View
            key={depth}
            style={[
              s.card,
              {
                transform: [
                  { translateY: depth * STACK.step },
                  { scale: 1 - depth * STACK.shrink },
                ],
              },
            ]}
            pointerEvents="none"
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            {card}
          </View>
        );
      })}

      <Animated.View
        {...responder.panHandlers}
        // Remounted per card by the caller's `key`, so the arrival runs once per person rather
        // than once per render, and the drag starts from rest.
        style={[
          s.card,
          {
            opacity: arrival,
            transform: [
              { translateX: drag.x },
              { translateY: Animated.add(drag.y, arrival.interpolate(LIFT_IN)) },
              { scale: arrival.interpolate(SCALE_IN) },
              { rotate: drag.x.interpolate(tilt()) },
            ],
          },
        ]}
      >
        {children}

        {/* The two stamps: feedback, never controls. Invisible at rest, full at the threshold,
            and hidden from assistive technology because a listener answers with the buttons. */}
        <Stamp said="yes" opacity={drag.x.interpolate(stampOpacity('yes'))} />
        <Stamp said="no" opacity={drag.x.interpolate(stampOpacity('no'))} />
      </Animated.View>
    </View>
  );
}

/**
 * One stamp — an outlined word, tilted, in the answer's own colour: **volt** for *Let's play*
 * and **white** for *Not today* (ADR-0169 §7). Top-left for a yes and top-right for a pass, so
 * each sits on the side the card is being dragged towards' opposite corner — where the mocks
 * draw them, and clear of the Level and the mark either way. The outline and the tilt are the
 * drawing's own; the words are the two answers' (`STAMP_WORDS`), uppercased by this style.
 */
function Stamp({
  said,
  opacity,
}: {
  readonly said: DeckExit;
  readonly opacity: Animated.AnimatedInterpolation<number>;
}) {
  const colour = said === 'yes' ? theme.color.volt : theme.color.surface;
  const way = wayOf(said);
  return (
    <Animated.View
      testID={`deck-stamp-${said}`}
      style={[
        s.stamp,
        said === 'yes' ? s.stampLeft : s.stampRight,
        { opacity, borderColor: colour, transform: [{ rotate: `${-way * STAMP.tilt}deg` }] },
      ]}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Text style={[s.stampWords, { color: colour }]}>{STAMP_WORDS[said]}</Text>
    </Animated.View>
  );
}

const LIFT_IN = { inputRange: [0, 1], outputRange: [STACK.step, 0] };
const SCALE_IN = { inputRange: [0, 1], outputRange: [1 - STACK.shrink, 1] };

const s = StyleSheet.create({
  // The height the phone gives the deck: every card in the stack takes the stage's box.
  stage: { flex: 1 },
  card: { ...StyleSheet.absoluteFillObject },
  stamp: {
    position: 'absolute',
    top: STAMP.top,
    borderWidth: STAMP.stroke,
    borderRadius: theme.radius.btn,
    paddingVertical: theme.space.xs,
    paddingHorizontal: theme.space.md,
  },
  stampLeft: { left: STAMP.inset },
  stampRight: { right: STAMP.inset },
  stampWords: {
    ...theme.type.deckStamp,
    textTransform: 'uppercase',
    ...theme.shadow.textOnMedia,
  },
});
