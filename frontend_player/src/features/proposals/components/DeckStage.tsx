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
 * `react-native-gesture-handler`, no `react-native-reanimated`** for the stage, though both are
 * in the app for the radar's field (ADR-0176) — because the chat row and the
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
 * The cards behind are the hand's next two people drawn as real cards, offset down, scaled
 * back and **faded** — 0,7 and 0,4, since #553 (Q90 of the Games grilling) — and only when that
 * many remain — never a placeholder (§3). They are absolutely laid
 * over the stage and the stage takes `flex: 1`, so all three cards are one size: the height the
 * phone gives the deck, not the height a card's own content happens to want. They are hidden
 * from assistive technology, because the top card is the one element and a listener does not
 * hear the queue.
 *
 * ## The card behind is promoted in place, and nothing blinks
 *
 * **Every card on the stage is one element for as long as it is on the stage**, keyed by the
 * caller, and the stage is never remounted per card. When the top card has gone the caller
 * hands the stage the same list one shorter, and the card that was behind becomes the top card
 * *as the element it already was*: its photograph is not decoded again, its wrapper is not
 * faded in again, and on the frame it takes over it stands exactly where it stood behind — one
 * step down, one shrink smaller — from where the arrival brings it to rest. So each card owns
 * its own `drag` and `arrival`, created at nought the first time the card is drawn and dropped
 * when it leaves the list: the card that flew stays where it flew until the caller takes it
 * away, and the card coming forward starts from rest, and neither has to wait for the other.
 * The cards behind draw off the **top card's** arrival too, one step further back at nought,
 * so a card leaving is followed by the whole stack coming forward as one motion
 * (`deckStageGeometry`'s `stackLift` and `stackScale`).
 *
 * This is what the three things a remount did in the same frame were: the answered card put
 * back straight by the *comes back straight* rule, because the screen clears `leaving` a tick
 * before the deck advances; the next card starting from `opacity: 0` and fading in over the
 * third card; and its photograph mounting again. Each read as a blink between the release and
 * the card under it.
 *
 * **A stack handed in standing arrives by its caller's motion, not this one** (`standing`, #863): the
 * Games deck swapped to its other kind brings its whole stack up into the stage as one, and a top
 * card that also came forward from a step back and a shrink smaller would be scaled under that rise.
 * Its cards stand in place from their first frame — the value starts there, so no frame is drawn
 * short of it — and every card after the swap arrives as ever.
 *
 * ## The durations live here rather than in the theme
 *
 * `theme.motion` is *"one entrance, one sheet, one popover, one fade"* and holds the shared
 * floors beside them; the engine fill's per-seat stagger is deliberately not there because *"it
 * is the court's own and belongs beside the animation it drives"*. The flight is the same case
 * — one surface, one pair of animations, numbers that mean nothing anywhere else — and the
 * settle borrows `motion.settle`, because a card coming to rest under a lifted finger is the
 * swipe row's own beat. The arrival borrows `motion.rise` for its length only: it is a **move,
 * and never a fade in from nothing**, because the card arriving was on the stage already, behind
 * the one that left, and a fade from nought would take away the very card the release is meant to
 * reveal. It brightens from the opacity it stood behind at, which is the same move read in light.
 *
 * ## Two decks stand on it, and the stamps are each deck's words
 *
 * Players' *Let's play* / *Not today* and a group's Games deck's *I'm in* / *Not this time*
 * ([#553](https://github.com/Raketa02/Raketa/issues/553), the screens A2.2) are one stage with two
 * pairs of words, so the words are the caller's — `stamps` — and the drawing is this file's. A
 * Games yes carries its price beside the words (*PAY · 32 zł*, *I'M IN · 32 zł*, Q124): the words
 * are uppercased by the stamp's style and the figure is not, because a figure is mono and `zł` is
 * not a word to shout.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { Animated, PanResponder, StyleSheet, Text, View } from 'react-native';

import { useHaptics } from '@/shared/lib/platform';
import { theme, useCollapsedPresentation } from '@/shared/ui';

import { STAMP_JOIN } from './deckPresentation';
import {
  claimsTheDrag,
  committed,
  crossedThreshold,
  stackLift,
  stackOpacity,
  stackScale,
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
 * The stamps' own drawing: a 3pt outline, a 12° tilt away from the card's centre, inset a large
 * step from the card's edge, and **90pt down** — under the Level's block, where the two swipe
 * mocks put them and clear of the mark either way — with the words a step in from the outline. The
 * drawing's own numbers, as the yes ground's glow keeps its centre and reach; the words and the
 * type role are the theme's. Exported for `deckStampFit.test.ts`, which holds the longest stamp,
 * *I'M IN · 32,50 zł*, to the narrowest phone's card.
 */
export const STAMP = {
  stroke: 3,
  tilt: 12,
  inset: theme.space.xl,
  top: 90,
  padX: theme.space.md,
  padY: theme.space.xs,
} as const;

/** What the screen answers when a drag commits — whether the card may fly. */
export type DragVerdict = 'taken' | 'withheld';

/**
 * What one stamp says — the answer's words, uppercased by the stamp, and a figure after them that
 * is not: *PAY · 32 zł*.
 */
export interface StampWords {
  readonly words: string;
  readonly figure?: string;
}

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
  /**
   * The cards on the stage, the top card first and then the cards behind, nearest first — real
   * cards or nothing, never placeholders. **Keyed by the caller**, by the person on the deal
   * they came off: the key is what lets a card that was behind become the top card as the same
   * element, and what gives each card its own motion.
   */
  readonly cards: readonly StagedCard[];
  /** What the two stamps say, for the card on top — see the module note. */
  readonly stamps: Readonly<Record<DeckExit, StampWords>>;
  /**
   * **The cards handed in now stand in place from their first frame** — a deck swapped to its other
   * kind, whose stack rises in as one by the deck's own motion (#863, `KindSwap`): the arrival — a
   * card coming forward from a step back and a shrink smaller — is not run for a card first drawn on
   * top while this is set. Absent, every card arrives.
   */
  readonly standing?: boolean;
}

/** One card on the stage, and what tells it from every other across renders. */
export interface StagedCard {
  readonly key: string;
  readonly card: ReactNode;
}

/**
 * One card's own motion — where the finger or the flight has put it, how far it has arrived,
 * and whether it has **gone**: a card that has gone stays where it went when the screen clears
 * `leaving`, where a card that came back is put straight.
 */
interface Motion {
  readonly drag: Animated.ValueXY;
  readonly arrival: Animated.Value;
  /** Drawn standing in place — no arrival to run (`standing`). */
  readonly standing: boolean;
  gone: boolean;
}

export function DeckStage({
  leaving,
  onAnswer,
  onLeft,
  cards,
  stamps,
  standing = false,
}: DeckStageProps) {
  const collapsed = useCollapsedPresentation();
  const haptics = useHaptics();
  /**
   * Each card's motion, by its key, for as long as it is on the stage. One value per phase, and
   * each drives every transform in it: a card is one object moving, where four values would be
   * four things able to be halfway through different animations. `drag` is where the finger has
   * put the card, and the flight continues from there. Under collapsed presentation a card has
   * arrived the moment it is drawn, so the cards behind stand in their places from the start.
   */
  const motions = useRef(new Map<string, Motion>()).current;
  const motionOf = (key: string): Motion => {
    const held = motions.get(key);
    if (held !== undefined) return held;
    const made: Motion = {
      drag: new Animated.ValueXY(),
      arrival: new Animated.Value(collapsed || standing ? 1 : 0),
      standing,
      gone: false,
    };
    motions.set(key, made);
    return made;
  };
  const top = cards[0];
  const motion = top === undefined ? undefined : motionOf(top.key);

  // Refs rather than dependencies: the pan handlers are created once and must not close over a
  // render's values, and the handlers close over the card that was answered — re-running the
  // flight because a parent re-rendered would restart a card mid-exit.
  const now = useRef({ leaving, collapsed, onAnswer, onLeft, haptics, motion });
  now.current = { leaving, collapsed, onAnswer, onLeft, haptics, motion };
  /** Whether the motor has ticked in this gesture — once per gesture, on the first crossing. */
  const ticked = useRef(false);

  const settle = useRef(() => {
    const { drag } = now.current.motion ?? {};
    if (drag === undefined) return;
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
        now.current.motion?.drag.setValue({ x: gesture.dx, y: gesture.dy * LIFT_SHARE });
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

  /** The cards that have left the list take their motion with them. */
  const keys = cards.map((card) => card.key).join('\n');
  useEffect(() => {
    const staged = new Set(keys.split('\n'));
    for (const key of [...motions.keys()]) if (!staged.has(key)) motions.delete(key);
  }, [keys, motions]);

  // The arrival: once per top card rather than once per render, from where it stood behind.
  useEffect(() => {
    if (motion === undefined) return;
    if (collapsed || motion.standing) {
      motion.arrival.setValue(1);
      return;
    }

    const rise = Animated.timing(motion.arrival, {
      toValue: 1,
      duration: theme.motion.rise,
      useNativeDriver: true,
    });
    rise.start();
    return () => rise.stop();
  }, [collapsed, motion]);

  useEffect(() => {
    if (motion === undefined) return;
    if (leaving === undefined) {
      // **A card that comes back comes back straight.** An answer refused puts the card on
      // screen again, and a stopped `Animated.Value` keeps whatever fraction of the flight it
      // reached — so without this the returned card sits shifted and turned, mid-exit, on the
      // one path the screen documents as recoverable. **A card that has gone is not a card that
      // came back**: the screen clears `leaving` the moment it hears, and advances the deck a
      // tick later, and a card put straight in between is the answered card flashing at the
      // centre of the stage before the next one replaces it.
      if (!motion.gone) motion.drag.setValue({ x: 0, y: 0 });
      return;
    }

    if (collapsed) {
      motion.gone = true;
      now.current.onLeft();
      return;
    }

    const flight = Animated.timing(motion.drag.x, {
      toValue: wayOf(leaving) * theme.size.deckSwipe.flight,
      duration: LEAVING_MS,
      useNativeDriver: true,
    });
    flight.start(({ finished }) => {
      if (!finished) return;
      motion.gone = true;
      now.current.onLeft();
    });

    // Unmounted mid-flight — the deal was replaced, or the tab was left. Stopping is what
    // keeps the callback from firing into a screen that is no longer there.
    return () => flight.stop();
  }, [leaving, collapsed, motion]);

  if (top === undefined || motion === undefined) return <View style={s.stage} />;

  return (
    <View style={s.stage}>
      {/* Deepest first, so the nearer card paints over the further one and the top card over
          both — the same keyed elements in a new order when a card leaves, which is what keeps
          the card coming forward the card it was. The cards behind are hidden from assistive
          technology: the top card is the one element. Every card draws off the top card's
          arrival, one step further back until it has arrived. */}
      {[...cards].reverse().map(({ key, card }, fromTheBack) => {
        const depth = cards.length - 1 - fromTheBack;
        const lift = motion.arrival.interpolate(stackLift(depth));
        const scale = motion.arrival.interpolate(stackScale(depth));
        const opacity = motion.arrival.interpolate(stackOpacity(depth));
        if (depth > 0) {
          return (
            <Animated.View
              key={key}
              style={[s.card, { opacity, transform: [{ translateY: lift }, { scale }] }]}
              pointerEvents="none"
              accessibilityElementsHidden
              importantForAccessibility="no-hide-descendants"
            >
              {card}
            </Animated.View>
          );
        }
        return (
          <Animated.View
            key={key}
            {...responder.panHandlers}
            style={[
              s.card,
              {
                opacity,
                transform: [
                  { translateX: motion.drag.x },
                  { translateY: Animated.add(motion.drag.y, lift) },
                  { scale },
                  { rotate: motion.drag.x.interpolate(tilt()) },
                ],
              },
            ]}
          >
            {card}

            {/* The two stamps: feedback, never controls. Invisible at rest, full at the
                threshold, and hidden from assistive technology because a listener answers with
                the buttons. */}
            <Stamp
              said="yes"
              stamp={stamps.yes}
              opacity={motion.drag.x.interpolate(stampOpacity('yes'))}
            />
            <Stamp
              said="no"
              stamp={stamps.no}
              opacity={motion.drag.x.interpolate(stampOpacity('no'))}
            />
          </Animated.View>
        );
      })}
    </View>
  );
}

/**
 * One stamp — an outlined word, tilted, in the answer's own colour: **volt** for *Let's play*
 * and **white** for *Not today* (ADR-0169 §7). Top-left for a yes and top-right for a pass, so
 * each sits on the side the card is being dragged towards' opposite corner — where the mocks
 * draw them, and clear of the Level and the mark either way. The outline and the tilt are the
 * drawing's own; the words are the caller's (`stamps`), uppercased by this style, and a figure
 * after them is drawn in mono and left as it is written.
 */
function Stamp({
  said,
  stamp,
  opacity,
}: {
  readonly said: DeckExit;
  readonly stamp: StampWords;
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
      <Text style={[s.stampWords, { color: colour }]}>
        {stamp.words}
        {stamp.figure === undefined ? null : (
          <Text style={s.stampFigure}>
            {STAMP_JOIN}
            {stamp.figure}
          </Text>
        )}
      </Text>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  // The height the phone gives the deck: every card in the stack takes the stage's box.
  stage: { flex: 1 },
  card: { ...StyleSheet.absoluteFillObject },
  stamp: {
    position: 'absolute',
    top: STAMP.top,
    borderWidth: STAMP.stroke,
    borderRadius: theme.radius.btn,
    paddingVertical: STAMP.padY,
    paddingHorizontal: STAMP.padX,
  },
  stampLeft: { left: STAMP.inset },
  stampRight: { right: STAMP.inset },
  stampWords: {
    ...theme.type.deckStamp,
    textTransform: 'uppercase',
    ...theme.shadow.textOnMedia,
  },
  // The price after the words: mono, as every figure is, and never uppercased — `zł` is a unit.
  stampFigure: { ...theme.num.xl, ...theme.tabular, textTransform: 'none' },
});
