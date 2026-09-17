/**
 * The **field** — the map of the night: the rings, the viewer's tile, every player at their
 * bearing and distance in the state their width demands, the zoom cluster on the right edge
 * and the footer on the bottom one
 * ([ADR-0174](../../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, [ADR-0176](../../../../../../docs/adr/0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md),
 * [`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.2–7.7).
 *
 * ## Three values on the UI thread, and every tile placed from them
 *
 * The live view is three Reanimated **shared values** — the scale and the two offsets of
 * `containerTransform` against the home view — written by the gestures and the flight on the
 * UI thread and read there by every animated style, so no frame of a drag, a pinch or a flight
 * passes through React or the JavaScript thread at all (ADR-0176 §2). **Every tile places
 * itself from them**: its anchor is a one-point view whose animated style reads the three
 * values, recovers the view (`viewFromTransform`) and translates the point to where
 * `toScreen` says the tile's spot is now, with the drawing hung off it — a face centred on
 * the point, a card's top-left on it. Nothing is laid out by React between gestures, and
 * **nothing is ever scaled**: a face is 24 or 30 pt and a card ~190 at every width (§7.9)
 * because no layer is drawn any other size. The field used to carry the lot on one scaled
 * transform with every tile counter-scaled by `1 / scale`; iOS rasterised that
 * 4 700-point-wide layer at its unscaled resolution and every tile at the floor was a blur of
 * a few pixels (ADR-0176 §2, amended 2026-09-17). One point and not none: iOS drops the
 * transform of a view with no size at all (`BaseViewProps::resolveTransform`), a translation
 * as much as a scale (ADR-0176 §1).
 *
 * ## What is JavaScript's: which rings, the footer, the counter
 *
 * The rings ride the same three values — each circle's centre and radius are an animated
 * prop, so a hairline is drawn at its live radius rather than scaled into a smear — but **which**
 * rings exist, the footer's count, the cluster's counter and the state every face is drawn in
 * are sentences, and sentences are React's. A reaction on the UI thread reads the live view off
 * the three values and tells JavaScript **only when a sentence would change**: the width to a
 * tenth of a kilometre, the count of points in view, or the zoom state — decided there, per
 * frame, with its dead-band, so a face changes state at the threshold and never at a release.
 * A pan that carries nobody across an edge says nothing; a pinch says a few words a frame; and
 * a re-render is the footer, the counter and a handful of ring labels, never the tiles, which
 * are memoised on what they draw.
 *
 * ## Gestures on the UI thread, and a tap is still a door
 *
 * `react-native-gesture-handler`'s pan and pinch, **simultaneous**, over the whole field. The
 * pan claims nothing until a finger has moved the intent distance, and the pinch needs two, so
 * a tap reaches the face or the card under it — they are doors — and the field's own background
 * press, under every tile, is the tap on empty ground: deselect, keep the zoom. A drag follows
 * the finger with no inertia and settles where it is let go; past the reach's edge it
 * **rubber-bands** — the field gives a little under the finger and springs back to the edge on
 * release (`rubberBand`, `boundCentre`). A pinch is continuous between the floor and the widest
 * stop and zooms **around the fingers**: the kilometre point under their first midpoint stays
 * under their midpoint, and the centre is **held** at the reach's edge rather than banded, so
 * a release has nothing to spring back from; while it lasts the pan only listens, and when one
 * finger lifts the drag is anchored afresh under the one that stays — on the recogniser's
 * **translation**, which stays continuous as fingers land and lift where their position jumps
 * by half a spread — so the field does not jump (ADR-0177 §1). **A pinch is over the moment
 * there are fewer than two fingers, whatever the recogniser says**: Android's pinch does not
 * end when one of the two lifts — it stays active on the one that remains and reports *that
 * finger* as the focal point, half a spread from the midpoint it was — so the hand-off is
 * made on the event's pointer count, and a one-finger pinch event moves nothing. The next ±
 * snaps to the ladder from wherever the pinch left off.
 *
 * ## A stack at the floor, and a tap that opens it
 *
 * At the floor — 1,5 km across, the narrowest the field goes — faces whose spots lie nearer
 * than one face is wide would still lie on one another, and closer is no longer an answer. They
 * are folded into a **stack**: one marker at their mean, saying how many (`domain/radarGeometry`'s
 * `stacksAt`, ADR-0177 §2). A tap on the marker **opens** it: the members fan out around it on
 * rings, a touch target from the marker and a face apart (`fanOut`), each with a hairline back
 * to it (`RadarLegs`), each a face that can be tapped — which flies to where the fan put them
 * and selects them, so the card opens at the fanned spot with the fan still standing. A tap on
 * the marker again, on empty field, or a zoom off the floor folds them back. The open stack is
 * this component's own state, by the stack's id: it survives a selection and dies with its
 * stack.
 *
 * ## The flight, and reduced motion
 *
 * A tap on a face flies to them — centred, at the 3 km stop or the width already held if that
 * is narrower — over `motion.flyTo`, `easeDecel`, and **selects on landing**; under collapsed
 * presentation the view is simply there and the selection is immediate. ± and ◉ travel the
 * same way over the shorter `motion.settle`. The three values are timed together, so the
 * transform is interpolated **linearly** and the rings and the words, reading the same values,
 * agree with it frame for frame. A gesture starting mid-flight stops it where it is.
 *
 * ## What is committed, and when
 *
 * The parent owns the view (`store/radarView`) and this component reports where a gesture, a
 * ±, a flight or ◉ **ended** — never each frame — so what is kept across tabs is a place the
 * player stopped at, and a re-render of the parent mid-gesture never fights the finger.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View, type LayoutChangeEvent } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  Easing,
  cancelAnimation,
  runOnJS,
  useAnimatedReaction,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { playerName } from '@/shared/formatting/playerName';
import { theme, useCollapsedPresentation } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  atFloor,
  boundCentre,
  containerTransform,
  dragged,
  fanOut,
  flyToView,
  homeView,
  inView,
  nextStopIn,
  nextStopOut,
  pinched,
  pointOf,
  stacksAt,
  tileState,
  toScreen,
  viewFromTransform,
  widestWidthKm,
  zoomState,
  type DragStart,
  type FieldBox,
  type KmPoint,
  type PinchStart,
  type RadarView,
  type ScreenPoint,
  type Stack,
  type ZoomState,
} from '../../domain/radarGeometry';
import { drawOrder, type RadarRow } from '../../domain/reading';
import { radarTileLabel } from '../accessibilityPresentation';
import { cardDistance } from '../radarPresentation';

import { RadarCard } from './RadarCard';
import { RadarFace, radarFaceBox } from './RadarFace';
import { RadarFooter, type RadarFooterState } from './RadarFooter';
import { RadarLegs, type Leg } from './RadarLegs';
import { RadarRings, type RadarTransform } from './RadarRings';
import { RADAR_STACK_BOX, RadarStack } from './RadarStack';
import { RadarZoomCluster } from './RadarZoomCluster';
import { YouTile } from './YouTile';

/** What the field has to draw: a reading, one on its way, or one that was refused. */
export type RadarStatus =
  | { readonly kind: 'loading' }
  | { readonly kind: 'failed'; readonly onTryAgain: () => void }
  | {
      readonly kind: 'read';
      readonly rows: readonly RadarRow[];
      /** The pool's own `radius_km_used` — the empty sentence's number, as the words say. */
      readonly radiusKmUsed: number;
    };

export interface RadarFieldProps {
  readonly status: RadarStatus;
  /** The profile's own radius: the reach the geometry is built on, known before the reading is. */
  readonly reachKm: number;
  readonly sport: Sport;
  readonly sportName: string;
  /** The viewer, for the tile at the origin. Undefined until the session's user is known. */
  readonly me: { readonly playerId: string; readonly photoUrl?: string } | undefined;
  /** Where the radar was left, or `undefined` for home. */
  readonly view: RadarView | undefined;
  readonly selectedId: string | undefined;
  /** A gesture, a ±, or a flight ended here. */
  readonly onViewChange: (view: RadarView) => void;
  /** ◉ has landed: home, deselected. */
  readonly onHome: () => void;
  /** A flight has landed on somebody. */
  readonly onSelect: (playerId: string) => void;
  /** A tap on empty field. */
  readonly onDeselect: () => void;
  /** A tap on a card. */
  readonly onOpenCard: (row: RadarRow) => void;
}

/** The two gestures, as a test finds them — `test-support/radarTouch` spells the same two ids. */
const RADAR_PAN_GESTURE = 'radar-pan';
const RADAR_PINCH_GESTURE = 'radar-pinch';

/** Nothing to draw yet, as one value, so the memo over it holds while the reading is on its way. */
const NO_ROWS: readonly RadarRow[] = [];

/** No stack, as one value, so the tile layer's memo holds through every width above the floor. */
const NO_STACKS: readonly Stack[] = [];

/**
 * Two players stack when their spots lie nearer than one face is wide — the closer face and
 * its ring — which is the one distance at which a finger cannot tell them apart (ADR-0177 §2).
 */
const STACK_WITHIN_PT = radarFaceBox('closer').width;

/**
 * An opened stack's fan: the first ring a touch target out from the marker, and a face's width
 * plus a step between neighbours and between rings.
 */
const FAN = {
  clearPt: theme.size.minTouch,
  stepPt: radarFaceBox('closer').width + theme.space.sm,
} as const;

/** How far a finger travels before the field claims a drag — the swipe row's own number, as the deck reads it. */
const INTENT = theme.size.swipeRow.intent;

/** What the UI thread tells JavaScript, and only when it changes: the width, the count, the state. */
interface Heard {
  readonly widthKm: number;
  readonly inView: number;
  /** Decided on the UI thread with its dead-band, so a release cannot flip it (the module note). */
  readonly zoom: ZoomState;
}

export function RadarField({
  status,
  reachKm,
  sport,
  sportName,
  me,
  view,
  selectedId,
  onViewChange,
  onHome,
  onSelect,
  onDeselect,
  onOpenCard,
}: RadarFieldProps) {
  const collapsed = useCollapsedPresentation();

  const [box, setBox] = useState<FieldBox | undefined>(undefined);
  const [footerHeight, setFooterHeight] = useState(0);

  const base = useMemo(() => homeView(reachKm), [reachKm]);
  const widest = widestWidthKm(reachKm);

  /** The transform's three values, on the UI thread. */
  const scale = useSharedValue(1);
  const x = useSharedValue(0);
  const y = useSharedValue(0);
  const transform = useMemo<RadarTransform>(() => ({ scale, x, y }), [scale, x, y]);
  /**
   * A flight's own clock, 0 to 1 beside the three values: the one of the four that always
   * moves, so its landing is the flight's. A value already at its target is finished the
   * moment it is asked, and a landing read off it would be a landing before take-off.
   */
  const progress = useSharedValue(1);

  /** The words' view of the field: the width, the count and the state, as the UI thread last said them. */
  const [heard, setHeard] = useState<Heard>(() => {
    const widthKm = (view ?? base).widthKm;
    return { widthKm, inView: 0, zoom: zoomState(widthKm) };
  });
  const zoom = heard.zoom;

  // The handlers are created once and read the render's values through this.
  const now = useRef({ box, base, collapsed, onViewChange, onSelect, onOpenCard });
  now.current = { box, base, collapsed, onViewChange, onSelect, onOpenCard };

  /** Where the field is drawn right now, read off the three values — exact, not the words'. */
  const live = useCallback((): RadarView => {
    const { box: field, base: home } = now.current;
    if (field === undefined) return view ?? home;
    return viewFromTransform({ scale: scale.value, x: x.value, y: y.value }, home, field);
  }, [scale, x, y, view]);

  /**
   * The view JavaScript last drew or was told of — what a later box is drawn from, since the
   * three values were computed against the box that is gone.
   */
  const held = useRef<RadarView>(view ?? base);

  /**
   * JavaScript knows the field is at `next`: held, and the counter told the exact width — the
   * UI thread speaks to a tenth of a kilometre, and a stop landed on is that stop and not the
   * hair short of it the last frame reported, which is what greys ± at the ladder's ends.
   */
  const knownAt = useCallback((next: RadarView) => {
    held.current = next;
    setHeard((words) =>
      words.widthKm === next.widthKm ? words : { ...words, widthKm: next.widthKm },
    );
  }, []);

  /** Draw the field at a view, at once. */
  const apply = useCallback(
    (next: RadarView) => {
      knownAt(next);
      const { box: field, base: home } = now.current;
      if (field === undefined) return;
      const t = containerTransform(next, home, field);
      scale.value = t.scale;
      x.value = t.x;
      y.value = t.y;
    },
    [knownAt, scale, x, y],
  );

  /** Where a gesture, a ±, or a flight ended: reported. Stable, so a worklet can hold it. */
  const commit = useCallback(
    (next: RadarView) => {
      knownAt(next);
      now.current.onViewChange(next);
    },
    [knownAt],
  );

  /**
   * The flight in progress: its number, so a landing can tell whether it is still the one
   * that was asked for, and what to do on arrival.
   */
  const flight = useRef<{ id: number; target: RadarView; landed: () => void } | undefined>(
    undefined,
  );
  const flights = useRef(0);

  const land = useCallback(
    (id: number, finished: boolean) => {
      const current = flight.current;
      if (current === undefined || current.id !== id) return;
      flight.current = undefined;
      if (!finished) return;
      commit(current.target);
      current.landed();
    },
    [commit],
  );

  /**
   * Travel to a view over `duration` and then do `landed` — or, under collapsed presentation,
   * be there. The three values are timed together under one easing, which is the transform
   * interpolated linearly (see the module note).
   */
  const travel = useCallback(
    (target: RadarView, duration: number, landed: () => void) => {
      const { box: field, base: home, collapsed: still } = now.current;
      flight.current = undefined;
      if (still || field === undefined) {
        apply(target);
        commit(target);
        landed();
        return;
      }
      const id = (flights.current += 1);
      flight.current = { id, target, landed };
      const to = containerTransform(target, home, field);
      const timing = { duration, easing: EASE };
      scale.value = withTiming(to.scale, timing);
      x.value = withTiming(to.x, timing);
      y.value = withTiming(to.y, timing);
      progress.value = 0;
      progress.value = withTiming(1, timing, (finished) => {
        runOnJS(land)(id, finished === true);
      });
    },
    [apply, commit, land, scale, x, y, progress],
  );

  /** A settle asked for by the UI thread: back to the reach's edge over `motion.settle`. */
  const settleTo = useCallback(
    (target: RadarView) => travel(target, theme.motion.settle, () => undefined),
    [travel],
  );

  /**
   * The gesture in hand: whether a pan is live and where it is anchored, where the pinch
   * started, and the pan's last travel — the recogniser's translation, which is continuous when
   * a finger lands or lifts, unlike the fingers' position.
   */
  const panning = useSharedValue(false);
  const panStart = useSharedValue<DragStart | undefined>(undefined);
  const pinchStart = useSharedValue<PinchStart | undefined>(undefined);
  const travelled = useSharedValue<ScreenPoint>({ x: 0, y: 0 });
  const active = useSharedValue(0);

  const gesture = useMemo(() => {
    const field = box;
    const home = base;
    const reach = reachKm;
    const widestKm = widest;

    const liveOnUI = (): RadarView => {
      'worklet';
      if (field === undefined) return home;
      return viewFromTransform({ scale: scale.value, x: x.value, y: y.value }, home, field);
    };
    const applyOnUI = (next: RadarView) => {
      'worklet';
      if (field === undefined) return;
      const t = containerTransform(next, home, field);
      scale.value = t.scale;
      x.value = t.x;
      y.value = t.y;
    };
    /** A gesture has begun: the flight, if any, stops where it is. */
    const grab = () => {
      'worklet';
      active.value += 1;
      cancelAnimation(scale);
      cancelAnimation(x);
      cancelAnimation(y);
      cancelAnimation(progress);
    };
    /** The last finger has lifted: back inside the reach if it went past, and committed. */
    const release = () => {
      'worklet';
      active.value -= 1;
      if (active.value > 0) return;
      const held = liveOnUI();
      const bound = boundCentre(held.centre, reach);
      // A hair, not an equality: a centre the pinch held at the edge comes back through the
      // transform an ulp outside it, and an ulp is not a band to spring back from.
      if (Math.abs(bound.x - held.centre.x) < SAME && Math.abs(bound.y - held.centre.y) < SAME) {
        runOnJS(commit)(held);
        return;
      }
      runOnJS(settleTo)({ centre: bound, widthKm: held.widthKm });
    };
    /**
     * The pinch is over — fewer than two fingers, or the recogniser's end, whichever is first —
     * and the drag, if a finger stays, is anchored afresh at the travel the pan last reported
     * and the view the pinch left, so the field does not jump to where that finger would have
     * dragged it alone (ADR-0177 §1). Idempotent: Android's recogniser ends after the fingers do.
     */
    const handOff = () => {
      'worklet';
      if (pinchStart.value === undefined) return;
      pinchStart.value = undefined;
      panStart.value = panning.value ? { at: travelled.value, view: liveOnUI() } : undefined;
    };

    const pan = Gesture.Pan()
      .withTestId(RADAR_PAN_GESTURE)
      .minDistance(INTENT)
      .averageTouches(true)
      .onStart((event) => {
        grab();
        panning.value = true;
        const at = { x: event.translationX, y: event.translationY };
        travelled.value = at;
        panStart.value = { at, view: liveOnUI() };
      })
      .onUpdate((event) => {
        const travel = { x: event.translationX, y: event.translationY };
        travelled.value = travel;
        // While two fingers are down the pinch is the one moving the field; the pan only
        // keeps track of how far it has travelled, for the moment the second one lifts.
        if (pinchStart.value !== undefined || field === undefined) return;
        const start = panStart.value ?? { at: travel, view: liveOnUI() };
        panStart.value = start;
        applyOnUI(dragged(start, travel, field, reach));
      })
      .onEnd(() => {
        panning.value = false;
        panStart.value = undefined;
        release();
      });

    const pinch = Gesture.Pinch()
      .withTestId(RADAR_PINCH_GESTURE)
      .onStart((event) => {
        grab();
        // The spread the recogniser reports as it activates, not 1: it activates once the
        // fingers have already moved a slop — a twelfth of their spread on Android — and a
        // first frame measured from 1 would zoom by that much at once.
        pinchStart.value = {
          spread: event.scale,
          mid: { x: event.focalX, y: event.focalY },
          view: liveOnUI(),
        };
      })
      .onUpdate((event) => {
        const start = pinchStart.value;
        if (start === undefined || field === undefined) return;
        // One finger is no pinch: Android's recogniser stays active on the finger that
        // remains and reports it as the focal point (the module note). Hand off, move nothing.
        if (event.numberOfPointers < 2) {
          handOff();
          return;
        }
        const fingers = { spread: event.scale, mid: { x: event.focalX, y: event.focalY } };
        applyOnUI(pinched(start, fingers, field, { reachKm: reach, widestKm }));
      })
      .onEnd(() => {
        handOff();
        release();
      });

    return Gesture.Simultaneous(pan, pinch);
  }, [
    box,
    base,
    reachKm,
    widest,
    scale,
    x,
    y,
    progress,
    active,
    panning,
    panStart,
    pinchStart,
    travelled,
    commit,
    settleTo,
  ]);

  // A flight is stopped with the field: the pane is remounted with every tab press, and an
  // animation that outlived it would keep writing a view nobody is drawing.
  useEffect(
    () => () => {
      flight.current = undefined;
      cancelAnimation(scale);
      cancelAnimation(x);
      cancelAnimation(y);
      cancelAnimation(progress);
    },
    [scale, x, y, progress],
  );

  // The three values are drawn from the held view once there is a box to draw them in — the
  // first layout, and any later one — since a view kept from an earlier visit is not the
  // identity the values start at, and values computed against a box that is gone are not
  // the view either.
  useEffect(() => {
    if (box !== undefined) apply(held.current);
  }, [box, apply]);

  // Drawn at the view the parent holds whenever it moves under this component — a reset, a
  // sport that keeps the view. Never mid-gesture or mid-flight, which is the finger's or the
  // flight's to finish.
  const wanted = view ?? base;
  useEffect(() => {
    if (box === undefined) {
      held.current = wanted;
      return;
    }
    if (flight.current !== undefined || active.value > 0) return;
    if (sameView(wanted, live())) return;
    apply(wanted);
  }, [box, wanted, apply, live, active]);

  // A reach that shrank under the view: the widest stop is the ceiling, so a view past it is
  // brought to it.
  useEffect(() => {
    const at = live();
    if (at.widthKm > widest) apply({ ...at, widthKm: widest });
  }, [widest, apply, live]);

  const rows = useMemo(() => (status.kind === 'read' ? status.rows : NO_ROWS), [status]);
  const points = useMemo<readonly KmPoint[]>(() => rows.map(pointOf), [rows]);

  // The words: the width to a tenth, and how many points are inside the box between the
  // header and the footer — the point where the field **draws** it, tested against the box
  // that stops at the footer's top edge. Said to JavaScript only when either changes.
  const said = useSharedValue<{
    tenths: number;
    seen: number;
    floor: boolean;
    zoom: ZoomState | undefined;
  }>({ tenths: -1, seen: -1, floor: false, zoom: undefined });
  const hear = useCallback(
    (widthKm: number, inView: number, zoom: ZoomState) => setHeard({ widthKm, inView, zoom }),
    [],
  );
  useAnimatedReaction(
    () => ({ scale: scale.value, x: x.value, y: y.value }),
    (t) => {
      if (box === undefined) return;
      const at = viewFromTransform(t, base, box);
      const visible = { width: box.width, height: Math.max(0, box.height - footerHeight) };
      let seen = 0;
      for (const point of points) {
        if (inView(toScreen(point, at, box), visible)) seen += 1;
      }
      const tenths = Math.round(at.widthKm * 10);
      // The floor is a sentence too — a stack may stand there — so reaching it is said the
      // moment it is reached, and not a tenth of a kilometre later.
      const floor = atFloor(at.widthKm);
      // So is the state a face is drawn in, with its dead-band over the state held — the UI
      // thread holds it, per frame, and JavaScript never derives it from a width it heard.
      const zoom = zoomState(at.widthKm, said.value.zoom);
      if (
        tenths === said.value.tenths &&
        seen === said.value.seen &&
        floor === said.value.floor &&
        zoom === said.value.zoom
      )
        return;
      said.value = { tenths, seen, floor, zoom };
      runOnJS(hear)(at.widthKm, seen, zoom);
    },
    [box, base, footerHeight, points, hear],
  );

  const zoomIn = () => {
    const at = live();
    const target = nextStopIn(at.widthKm);
    if (target === undefined) return;
    travel({ ...at, widthKm: target }, theme.motion.settle, () => undefined);
  };
  const zoomOut = () => {
    const at = live();
    const target = nextStopOut(at.widthKm, widest);
    if (target === undefined) return;
    travel({ ...at, widthKm: target }, theme.motion.settle, () => undefined);
  };
  const goHome = () => travel(base, theme.motion.settle, onHome);
  /**
   * A face was tapped: fly, and select on landing. A fanned face flies to where it is drawn, at
   * the width held, so the fan stays open around the one selected. Stable, so the tile layer's
   * memo holds.
   */
  const flyTo = useCallback(
    (row: RadarRow, fannedAt?: KmPoint) =>
      travel(
        fannedAt === undefined
          ? flyToView(row, live().widthKm)
          : { centre: fannedAt, widthKm: live().widthKm },
        theme.motion.flyTo,
        () => now.current.onSelect(row.playerId),
      ),
    [travel, live],
  );
  /** A card was tapped: the record. Stable, for the same reason. */
  const openCard = useCallback((row: RadarRow) => now.current.onOpenCard(row), []);

  /**
   * The stacks at the width the field last spoke — none above the floor, and at the floor
   * every group of faces a finger could not tell apart (ADR-0177 §2). Held as one value while
   * there are none, so the tile layer is not rebuilt for a width that changed nothing.
   */
  const stacks = useMemo(() => {
    if (box === undefined) return NO_STACKS;
    const found = stacksAt(rows, heard.widthKm, box, STACK_WITHIN_PT);
    return found.length === 0 ? NO_STACKS : found;
  }, [rows, heard.widthKm, box]);

  /** The stack tapped open, by id — so it survives a selection and closes with its stack. */
  const [openStackId, setOpenStackId] = useState<string | undefined>(undefined);
  const open = stacks.find((stack) => stack.id === openStackId);
  useEffect(() => {
    if (openStackId !== undefined && open === undefined) setOpenStackId(undefined);
  }, [openStackId, open]);
  const fanned = useMemo(() => {
    if (open === undefined || box === undefined) return new Map<string, KmPoint>();
    return new Map(fanOut(open, box, FAN).map((member) => [member.playerId, member.at]));
  }, [open, box]);
  const legs = useMemo<readonly Leg[]>(() => {
    if (open === undefined) return [];
    return [...fanned].map(([playerId, at]) => ({ key: playerId, from: open.centre, to: at }));
  }, [open, fanned]);
  /** A tap on the marker: spread them, or fold them back. */
  const toggleStack = useCallback(
    (stack: Stack) => setOpenStackId((held) => (held === stack.id ? undefined : stack.id)),
    [],
  );
  /** A tap on empty field: deselect, fold any open stack, keep the zoom. */
  const onEmptyPress = () => {
    setOpenStackId(undefined);
    onDeselect();
  };

  const footer: RadarFooterState =
    status.kind === 'loading'
      ? { kind: 'loading' }
      : status.kind === 'failed'
        ? { kind: 'failed', onTryAgain: status.onTryAgain }
        : rows.length === 0
          ? { kind: 'empty', reachKm: status.radiusKmUsed, sportName }
          : {
              kind: 'reading',
              inView: heard.inView,
              offScreen: Math.max(0, rows.length - heard.inView),
              zoom,
              stacked: stacks.length > 0,
            };

  /**
   * The tile layer, **built only when what it draws changes** — the rows, the selection, the
   * zoom state, the reach, the box — and never on a frame of the live view: the transform is
   * what moves per frame, and a hundred anchors re-rendered sixty times a second would be the
   * layout this component exists not to do. Every handler it closes over is stable.
   */
  const tiles = useMemo(() => {
    if (box === undefined) return null;
    const stackOf = new Map<string, Stack>();
    for (const stack of stacks) for (const member of stack.members) stackOf.set(member, stack);

    const tile = (row: RadarRow) => {
      const inOpen = open !== undefined && stackOf.get(row.playerId) === open;
      // Drawn where the row is — or, while its stack is open, where the fan put it.
      const spot = inOpen ? (fanned.get(row.playerId) ?? pointOf(row)) : pointOf(row);
      const label = radarTileLabel({
        name: playerName({ kind: 'player', name: row.card.name }),
        distance: cardDistance(row.distanceKm),
        sportName,
        level: row.card.level,
      });
      // The card is the selection's and nobody else's (ADR-0176 §3).
      const state = tileState(zoom, row.playerId === selectedId);
      return (
        <Anchor key={row.playerId} spot={spot} transform={transform} base={base} field={box}>
          {state === 'card' ? (
            <View style={s.cardAt}>
              <RadarCard
                row={row}
                sport={sport}
                accessibilityLabel={label}
                onPress={() => openCard(row)}
              />
            </View>
          ) : (
            <View style={centred(radarFaceBox(state), state === 'closer')}>
              <RadarFace
                playerId={row.playerId}
                photoUrl={row.card.photoUrl}
                level={row.card.level}
                state={state}
                accessibilityLabel={label}
                onPress={() => flyTo(row, inOpen ? fanned.get(row.playerId) : undefined)}
              />
            </View>
          )}
        </Anchor>
      );
    };
    const marker = (stack: Stack) => (
      <Anchor key={stack.id} spot={stack.centre} transform={transform} base={base} field={box}>
        <View style={centred(RADAR_STACK_BOX)}>
          <RadarStack
            members={stack.members.length}
            open={stack === open}
            onPress={() => toggleStack(stack)}
          />
        </View>
      </Anchor>
    );

    // Farther first, so nearer players paint above; a folded stack's members are its marker
    // and are not drawn; the open stack's fan above the field and its marker above the fan;
    // the selected — the one card — above everybody.
    const ordered = drawOrder(rows, selectedId);
    const selected = ordered.find((row) => row.playerId === selectedId);
    const folded = (row: RadarRow) => {
      const stack = stackOf.get(row.playerId);
      return stack !== undefined && stack !== open;
    };
    return [
      ...ordered
        .filter((row) => row !== selected && !folded(row) && stackOf.get(row.playerId) !== open)
        .map(tile),
      ...stacks.filter((stack) => stack !== open).map(marker),
      ...ordered.filter((row) => row !== selected && stackOf.get(row.playerId) === open).map(tile),
      ...(open === undefined ? [] : [marker(open)]),
      ...(selected === undefined ? [] : [tile(selected)]),
    ];
  }, [
    box,
    rows,
    selectedId,
    zoom,
    base,
    sport,
    sportName,
    transform,
    openCard,
    flyTo,
    stacks,
    open,
    fanned,
    toggleStack,
  ]);

  const you = useMemo(() => {
    if (box === undefined || me === undefined) return null;
    return (
      <Anchor spot={ORIGIN} transform={transform} base={base} field={box}>
        <View style={centred(YOU_BOX)}>
          <YouTile playerId={me.playerId} photoUrl={me.photoUrl} />
        </View>
      </Anchor>
    );
  }, [box, me, base, transform]);

  // The field's box.
  const onLayout = (event: LayoutChangeEvent) => {
    const { width, height } = event.nativeEvent.layout;
    setBox({ width, height });
  };

  return (
    <GestureDetector gesture={gesture}>
      <View style={s.field} onLayout={onLayout} testID="radar-field">
        {/* A tap on empty field: deselect, keep the zoom. Under every tile, and no element — ◉
            is the accessible way to let somebody go. */}
        <Pressable
          style={StyleSheet.absoluteFill}
          onPress={onEmptyPress}
          testID="radar-field-empty"
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />

        {box === undefined ? null : (
          <RadarRings transform={transform} base={base} field={box} widthKm={heard.widthKm} />
        )}

        {box === undefined ? null : (
          <RadarLegs transform={transform} base={base} field={box} legs={legs} />
        )}

        {box === undefined ? null : (
          <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
            {you}
            {/* Farther first, so nearer players paint above; the selected last, above everybody. */}
            {tiles}
          </View>
        )}

        <RadarZoomCluster
          widthKm={heard.widthKm}
          canZoomIn={nextStopIn(heard.widthKm) !== undefined}
          canZoomOut={nextStopOut(heard.widthKm, widest) !== undefined}
          onZoomIn={zoomIn}
          onZoomOut={zoomOut}
          onHome={goHome}
        />

        <RadarFooter
          state={footer}
          onLayout={(event) => setFooterHeight(event.nativeEvent.layout.height)}
        />
      </View>
    </GestureDetector>
  );
}

/**
 * A tile's anchor: a one-point view translated, on the UI thread, to where the live view draws
 * the tile's kilometre spot — the three values read on every frame, the view recovered from
 * them and the spot put through `toScreen`, exactly as a ring's centre is. The drawing hangs
 * off it — centred on it for a face, from its top-left for a card — and `overflow: visible` is
 * stated because the anchor has no box of its own for its child to be inside. One point and
 * not none, for the module note's reason; never scaled, for the same note's other reason.
 */
function Anchor({
  spot,
  transform,
  base,
  field,
  children,
}: {
  readonly spot: KmPoint;
  readonly transform: RadarTransform;
  readonly base: RadarView;
  readonly field: FieldBox;
  readonly children: ReactNode;
}) {
  const placed = useAnimatedStyle(() => {
    const live = viewFromTransform(
      { scale: transform.scale.value, x: transform.x.value, y: transform.y.value },
      base,
      field,
    );
    const at = toScreen(spot, live, field);
    return { transform: [{ translateX: at.x - ANCHOR / 2 }, { translateY: at.y - ANCHOR / 2 }] };
  });
  return (
    <Animated.View style={[s.anchor, placed]} pointerEvents="box-none">
      {children}
    </Animated.View>
  );
}

/** The viewer's kilometre point, which their tile stands on and every ring is centred on. */
const ORIGIN: KmPoint = { x: 0, y: 0 };

/** The anchor's side: one point, so its centre is the point and its transform is kept. */
const ANCHOR = 1;

/** A drawing of `box` centred on the anchor — or, with a level hanging below, its face centred. */
function centred(box: { width: number; height: number }, faceOnly = false) {
  return {
    position: 'absolute' as const,
    left: ANCHOR / 2 - box.width / 2,
    top: ANCHOR / 2 - (faceOnly ? box.width / 2 : box.height / 2),
  };
}

const YOU_BOX = {
  width: theme.size.radar.you + 2 * theme.size.radar.stroke,
  height: theme.size.radar.you + 2 * theme.size.radar.stroke,
};

/** The prototype's decelerating curve, as the theme records it. */
const EASE = Easing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/** A hair: two views this close are one, so a round trip through the transform is not a move. */
const SAME = 1e-6;

function sameView(a: RadarView, b: RadarView): boolean {
  return (
    Math.abs(a.widthKm - b.widthKm) < SAME &&
    Math.abs(a.centre.x - b.centre.x) < SAME &&
    Math.abs(a.centre.y - b.centre.y) < SAME
  );
}

const s = StyleSheet.create({
  field: { flex: 1, overflow: 'hidden' },
  anchor: {
    position: 'absolute',
    left: 0,
    top: 0,
    width: ANCHOR,
    height: ANCHOR,
    overflow: 'visible',
  },
  cardAt: { position: 'absolute', left: ANCHOR / 2, top: ANCHOR / 2 },
});
