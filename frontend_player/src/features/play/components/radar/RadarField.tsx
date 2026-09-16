/**
 * The **field** — the map of the night: the rings, the viewer's tile, every player at their
 * bearing and distance in the state their width demands, the zoom cluster on the right edge
 * and the footer on the bottom one
 * ([ADR-0174](../../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, [`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.2–7.7).
 *
 * ## One transform, on the native driver, and tiles laid out once
 *
 * Every tile is absolutely positioned **once**, at the home view's scale — `domain/radarGeometry`'s
 * `toScreen` under `homeView(reach)` — inside one `Animated.View` whose transform carries the
 * lot to wherever the live view is (`containerTransform`). A pan is that transform's offset
 * moving, a pinch its scale, ± and the flight both, and nothing is laid out again until a
 * gesture ends. The three values — the scale and the two offsets — are native-driven, and every
 * tile **counter-scales** by the shared `Animated.divide(1, scale)` so a face is always 24 or
 * 30 pt and a card always ~190 whatever the pinch is doing (§7.9). A tile's anchor is a 0 × 0
 * view at the point with the drawing hung off it, so the counter-scale is about the point
 * itself: a face stays centred on its spot and a card keeps its top-left there.
 *
 * ## What is JavaScript's: the rings, the footer, the counter
 *
 * The rings cannot ride the transform — a hairline scaled by twelve under a pinch is a smear
 * — and the footer's count and the cluster's counter are sentences over the live view. So a
 * `live` view is kept in React state beside the native values and updated on every move:
 * a handful of circles and two sentences, which is cheap, where re-laying-out a hundred tiles
 * would not be. During a flight the JavaScript side reads the view off the **same** linear
 * interpolation of the transform the native side is animating (`viewFromTransform` over
 * `betweenTransforms`), so the two agree frame for frame and land together.
 *
 * ## Raw touches, and no gesture library
 *
 * `PanResponder`, as the deck and the swipe row (ADR-0165 §6). The field never claims the touch
 * on the press — a face and a card are doors and a tap has to reach them — and claims on a
 * **move**: one finger past the intent distance is a drag, two fingers is a pinch. A drag
 * follows the finger with no inertia and settles where it is let go; past the reach's edge it
 * **rubber-bands** — the field gives a little under the finger and springs back to the edge on
 * release (`rubberBand`, `boundCentre`). A pinch is continuous between the floor and the widest
 * stop and zooms **around the fingers**: the kilometre point under the fingers' first midpoint
 * stays under their midpoint. The next ± snaps to the ladder from wherever the pinch left off.
 * A tap on empty field is the background's own press, under the tiles: deselect, keep the zoom.
 *
 * ## The flight, and reduced motion
 *
 * A tap on a face flies to them — centred, at the 3 km stop — over `motion.flyTo`, `easeDecel`,
 * and **selects on landing**; under collapsed presentation the view is simply there and the
 * selection is immediate. ± and ◉ travel the same way over the shorter `motion.settle`. A
 * gesture starting mid-flight stops it where it is.
 *
 * ## What is committed, and when
 *
 * The parent owns the view (`store/radarView`) and this component reports where a gesture, a
 * ±, a flight or ◉ **ended** — never each frame — so what is kept across tabs is a place the
 * player stopped at, and a re-render of the parent mid-gesture never fights the finger.
 */

import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import {
  Animated,
  Easing,
  PanResponder,
  Pressable,
  StyleSheet,
  View,
  type GestureResponderEvent,
  type LayoutChangeEvent,
} from 'react-native';

import { playerName } from '@/shared/formatting/playerName';
import { theme, useCollapsedPresentation } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  WIDTH_FLOOR_KM,
  betweenTransforms,
  boundCentre,
  containerTransform,
  flyToView,
  focusOf,
  homeView,
  inView,
  nextStopIn,
  nextStopOut,
  pointOf,
  ptPerKm,
  ringsFor,
  rubberBand,
  toKm,
  toScreen,
  viewFromTransform,
  widestWidthKm,
  zoomState,
  type FieldBox,
  type RadarView,
  type ScreenPoint,
  type ZoomState,
} from '../../domain/radarGeometry';
import { drawOrder, type RadarRow } from '../../domain/reading';
import { radarTileLabel } from '../accessibilityPresentation';
import { cardDistance } from '../radarPresentation';

import { RadarCard } from './RadarCard';
import { RadarFace, radarFaceBox } from './RadarFace';
import { RadarFooter, type RadarFooterState } from './RadarFooter';
import { RadarRings } from './RadarRings';
import { RadarZoomCluster } from './RadarZoomCluster';
import { YouTile } from './YouTile';

/** What the field has to draw: a reading, one on its way, or one that was refused. */
export type RadarStatus =
  | { readonly kind: 'loading' }
  | { readonly kind: 'failed'; readonly onTryAgain: () => void }
  | { readonly kind: 'read'; readonly rows: readonly RadarRow[]; readonly reachKm: number };

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

/** Nothing to draw yet, as one value, so the memo over it holds while the reading is on its way. */
const NO_ROWS: readonly RadarRow[] = [];

/** How often, at most, the JavaScript side redraws the rings and the words during a flight: a frame. */
const WORDS_FRAME_MS = 16;

/** How far a finger travels before the field claims a drag — the swipe row's own number. */
const INTENT = theme.size.deckSwipe.intent;

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
  /** The field's place in the window, so a touch's page coordinates become field coordinates. */
  const origin = useRef({ x: 0, y: 0 });
  const root = useRef<View>(null);

  const base = useMemo(() => homeView(reachKm), [reachKm]);
  const widest = widestWidthKm(reachKm);

  /** The live view — where the field is drawn right now — in state for the rings and the words. */
  const [live, setLive] = useState<RadarView>(view ?? base);
  const liveRef = useRef(live);
  /** The zoom state held, for the dead-band over the thresholds. */
  const zoomRef = useRef<ZoomState>(zoomState(live.widthKm));
  const zoom = (zoomRef.current = zoomState(live.widthKm, zoomRef.current));

  /** The transform's three values, native-driven, and the counter-scale every tile shares. */
  const scale = useRef(new Animated.Value(1)).current;
  const x = useRef(new Animated.Value(0)).current;
  const y = useRef(new Animated.Value(0)).current;
  const inverse = useMemo(() => Animated.divide(1, scale), [scale]);
  /** The flight in progress, so a gesture can stop it. */
  const flight = useRef<Animated.CompositeAnimation | undefined>(undefined);

  // The handlers are created once and read the render's values through this.
  const now = useRef({ box, base, widest, reachKm, collapsed, onViewChange, onSelect, onOpenCard });
  now.current = { box, base, widest, reachKm, collapsed, onViewChange, onSelect, onOpenCard };

  /** Draw the field at a view: the native values, and the state the words are written from. */
  const apply = useRef((next: RadarView) => {
    const { box: field, base: home } = now.current;
    liveRef.current = next;
    if (field !== undefined) {
      const t = containerTransform(next, home, field);
      scale.setValue(t.scale);
      x.setValue(t.x);
      y.setValue(t.y);
    }
    setLive(next);
  }).current;

  /** Where a gesture, a ±, or a flight ended: drawn there, and reported. */
  const commit = useRef((next: RadarView) => {
    apply(next);
    now.current.onViewChange(next);
  }).current;

  /**
   * Travel to a view over `duration` and then do `landed` — or, under collapsed presentation,
   * be there. The transform is interpolated linearly on the native driver and the words follow
   * the same interpolation in JavaScript (see the module note).
   */
  const travel = useRef((target: RadarView, duration: number, landed: () => void) => {
    flight.current?.stop();
    const { box: field, base: home, collapsed: still } = now.current;
    if (still || field === undefined) {
      commit(target);
      landed();
      return;
    }
    const from = containerTransform(liveRef.current, home, field);
    const to = containerTransform(target, home, field);
    const progress = new Animated.Value(0);
    const timing = { duration, easing: EASE, useNativeDriver: true };
    const words = Animated.timing(progress, { ...timing, toValue: 1, useNativeDriver: false });
    // The words follow at a frame's pace and never faster: the rings and two sentences are
    // re-drawn from the view at most once per `WORDS_FRAME_MS`, whatever rate the listener is
    // called at — and the landing is drawn by `commit`, exactly.
    let painted = -Infinity;
    progress.addListener(({ value }) => {
      const at = Date.now();
      if (at - painted < WORDS_FRAME_MS) return;
      painted = at;
      const between = betweenTransforms(from, to, value);
      const along = viewFromTransform(between, home, field);
      liveRef.current = along;
      setLive(along);
    });
    const run = Animated.parallel([
      Animated.timing(scale, { ...timing, toValue: to.scale }),
      Animated.timing(x, { ...timing, toValue: to.x }),
      Animated.timing(y, { ...timing, toValue: to.y }),
      words,
    ]);
    flight.current = run;
    run.start(({ finished }) => {
      progress.removeAllListeners();
      flight.current = undefined;
      if (!finished) return;
      commit(target);
      landed();
    });
  }).current;

  /** The gesture in hand: where it started, and — for a pinch — the fingers' first spread. */
  const gesture = useRef<{
    pan?: { at: ScreenPoint; view: RadarView };
    pinch?: { spread: number; mid: ScreenPoint; view: RadarView };
  }>({});

  const responder = useRef(
    PanResponder.create({
      // Never on the press: a face and a card are doors, and a tap has to reach them.
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (event, state) =>
        state.numberActiveTouches >= 2 || Math.hypot(state.dx, state.dy) >= INTENT,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        flight.current?.stop();
        flight.current = undefined;
        gesture.current = {};
      },
      onPanResponderMove: (event) => {
        const { box: field, reachKm: reach, widest: widestKm } = now.current;
        if (field === undefined) return;
        const touches = touchesOf(event, origin.current);
        const held = liveRef.current;

        if (touches.length >= 2) {
          const [a, b] = touches as [ScreenPoint, ScreenPoint];
          const spread = Math.hypot(a.x - b.x, a.y - b.y);
          const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
          const pinch = gesture.current.pinch ?? { spread, mid, view: held };
          gesture.current = { pinch };
          if (pinch.spread === 0) return;
          // Continuous between the floor and the widest stop, around the fingers: the point
          // that was under their first midpoint stays under their midpoint now.
          const widthKm = Math.min(
            widestKm,
            Math.max(WIDTH_FLOOR_KM, (pinch.view.widthKm * pinch.spread) / spread),
          );
          const under = toKm(pinch.mid, pinch.view, field);
          const s = ptPerKm(field, widthKm);
          const focus = focusOf(field);
          const centre = {
            x: under.x - (mid.x - focus.x) / s,
            y: under.y + (mid.y - focus.y) / s,
          };
          apply({ centre: rubberBand(centre, reach), widthKm });
          return;
        }

        const [finger] = touches;
        if (finger === undefined) return;
        // One finger. Anchored afresh when the second finger has just lifted, so the field does
        // not jump to where the first finger would have dragged it alone.
        const pan = gesture.current.pan ?? { at: finger, view: held };
        gesture.current = { pan };
        const s = ptPerKm(field, pan.view.widthKm);
        const centre = {
          x: pan.view.centre.x - (finger.x - pan.at.x) / s,
          y: pan.view.centre.y + (finger.y - pan.at.y) / s,
        };
        apply({ centre: rubberBand(centre, reach), widthKm: pan.view.widthKm });
      },
      onPanResponderRelease: () => settle(),
      onPanResponderTerminate: () => settle(),
    }),
  ).current;

  /** The finger has lifted: back inside the reach if it went past, and committed. */
  const settle = useRef(() => {
    const held = liveRef.current;
    const bound = boundCentre(held.centre, now.current.reachKm);
    gesture.current = {};
    if (bound.x === held.centre.x && bound.y === held.centre.y) {
      commit(held);
      return;
    }
    travel({ centre: bound, widthKm: held.widthKm }, theme.motion.settle, () => undefined);
  }).current;

  // The field's box, and where it is in the window.
  const onLayout = (event: LayoutChangeEvent) => {
    const { width, height } = event.nativeEvent.layout;
    setBox({ width, height });
    root.current?.measureInWindow((left, top) => {
      origin.current = { x: left, y: top };
    });
  };

  // A flight is stopped with the field: the pane is remounted with every tab press, and an
  // animation that outlived it would keep writing a view nobody is drawing.
  useEffect(() => () => flight.current?.stop(), []);

  // The native values are drawn from the live view once there is a box to draw them in — the
  // first layout, and any later one — since a view kept from an earlier visit is not the
  // identity the values start at.
  useEffect(() => {
    if (box !== undefined) apply(liveRef.current);
  }, [box, apply]);

  // Drawn at the view the parent holds whenever it moves under this component — a reset, a
  // sport that keeps the view. Never mid-gesture or mid-flight, which is the finger's or the
  // flight's to finish.
  const wanted = view ?? base;
  useEffect(() => {
    if (box === undefined || flight.current !== undefined) return;
    if (gesture.current.pan !== undefined || gesture.current.pinch !== undefined) return;
    if (sameView(wanted, liveRef.current)) return;
    apply(wanted);
  }, [box, wanted, apply]);

  // A reach that shrank under the view: the widest stop is the ceiling, so a view past it is
  // brought to it.
  useEffect(() => {
    if (liveRef.current.widthKm > widest) apply({ ...liveRef.current, widthKm: widest });
  }, [widest, apply]);

  const zoomIn = () => {
    const target = nextStopIn(liveRef.current.widthKm);
    if (target === undefined) return;
    travel({ ...liveRef.current, widthKm: target }, theme.motion.settle, () => undefined);
  };
  const zoomOut = () => {
    const target = nextStopOut(liveRef.current.widthKm, widest);
    if (target === undefined) return;
    travel({ ...liveRef.current, widthKm: target }, theme.motion.settle, () => undefined);
  };
  const goHome = () => travel(base, theme.motion.settle, onHome);
  /** A face was tapped: fly, and select on landing. Stable, so the tile layer's memo holds. */
  const flyTo = useRef((row: RadarRow) =>
    travel(flyToView(row), theme.motion.flyTo, () => now.current.onSelect(row.playerId)),
  ).current;
  /** A card was tapped: the record. Stable, for the same reason. */
  const openCard = useRef((row: RadarRow) => now.current.onOpenCard(row)).current;

  const rows = useMemo(() => (status.kind === 'read' ? status.rows : NO_ROWS), [status]);

  // The words: how many points are inside the box between the header and the footer.
  const counted = useMemo(() => {
    if (box === undefined) return { inView: 0, offScreen: 0 };
    const visible = { width: box.width, height: Math.max(0, box.height - footerHeight) };
    const seen = rows.filter((row) => inView(toScreen(pointOf(row), live, visible), visible));
    return { inView: seen.length, offScreen: rows.length - seen.length };
  }, [box, footerHeight, rows, live]);

  const footer: RadarFooterState =
    status.kind === 'loading'
      ? { kind: 'loading' }
      : status.kind === 'failed'
        ? { kind: 'failed', onTryAgain: status.onTryAgain }
        : rows.length === 0
          ? { kind: 'empty', reachKm: status.reachKm, sportName }
          : { kind: 'reading', inView: counted.inView, offScreen: counted.offScreen, zoom };

  const rings = box === undefined ? [] : ringsFor(box, live.widthKm);
  const viewer = box === undefined ? undefined : toScreen({ x: 0, y: 0 }, live, box);

  /**
   * The tile layer, **built only when what it draws changes** — the rows, the selection, the
   * zoom state, the reach, the box — and never on a frame of the live view: the transform is
   * what moves per frame, and a hundred anchors re-rendered sixty times a second would be the
   * layout this component exists not to do. Every handler it closes over is stable.
   */
  const tiles = useMemo(() => {
    if (box === undefined) return null;
    return drawOrder(rows, selectedId).map((row) => {
      const at = toScreen(pointOf(row), base, box);
      const label = radarTileLabel({
        name: playerName({ kind: 'player', name: row.card.name }),
        distance: cardDistance(row.distanceKm),
        sportName,
        level: row.card.level,
      });
      const state = row.playerId === selectedId ? 'closest' : zoom;
      return (
        <Anchor key={row.playerId} at={at} inverse={inverse}>
          {state === 'closest' ? (
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
                onPress={() => flyTo(row)}
              />
            </View>
          )}
        </Anchor>
      );
    });
  }, [box, rows, selectedId, zoom, base, sport, sportName, inverse, openCard, flyTo]);

  return (
    <View
      ref={root}
      style={s.field}
      onLayout={onLayout}
      testID="radar-field"
      {...responder.panHandlers}
    >
      {/* A tap on empty field: deselect, keep the zoom. Under every tile, and no element — ◉ is
          the accessible way to let somebody go. */}
      <Pressable
        style={StyleSheet.absoluteFill}
        onPress={onDeselect}
        testID="radar-field-empty"
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      />

      {viewer === undefined ? null : <RadarRings centre={viewer} rings={rings} />}

      {box === undefined ? null : (
        <Animated.View
          style={[
            StyleSheet.absoluteFill,
            { transform: [{ translateX: x }, { translateY: y }, { scale }] },
          ]}
          pointerEvents="box-none"
        >
          {me === undefined ? null : (
            <Anchor at={toScreen({ x: 0, y: 0 }, base, box)} inverse={inverse}>
              <View style={centred(YOU_BOX)}>
                <YouTile playerId={me.playerId} photoUrl={me.photoUrl} />
              </View>
            </Anchor>
          )}

          {/* Farther first, so nearer players paint above; the selected last, above everybody. */}
          {tiles}
        </Animated.View>
      )}

      <RadarZoomCluster
        widthKm={live.widthKm}
        canZoomIn={nextStopIn(live.widthKm) !== undefined}
        canZoomOut={nextStopOut(live.widthKm, widest) !== undefined}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onHome={goHome}
      />

      <RadarFooter
        state={footer}
        onLayout={(event) => setFooterHeight(event.nativeEvent.layout.height)}
      />
    </View>
  );
}

/**
 * A tile's anchor: a 0 × 0 view at the point, counter-scaled about it. The drawing hangs off
 * it — centred on it for a face, from its top-left for a card — and `overflow: visible` is
 * stated because the anchor has no box of its own for its child to be inside.
 */
function Anchor({
  at,
  inverse,
  children,
}: {
  readonly at: ScreenPoint;
  readonly inverse: Animated.AnimatedDivision<number>;
  readonly children: ReactNode;
}) {
  return (
    <Animated.View
      style={[s.anchor, { left: at.x, top: at.y, transform: [{ scale: inverse }] }]}
      pointerEvents="box-none"
    >
      {children}
    </Animated.View>
  );
}

/** A drawing of `box` centred on the anchor — or, with a level hanging below, its face centred. */
function centred(box: { width: number; height: number }, faceOnly = false) {
  return {
    position: 'absolute' as const,
    left: -box.width / 2,
    top: faceOnly ? -box.width / 2 : -box.height / 2,
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

/** The two fingers' — or the one finger's — positions, in the field's own coordinates. */
function touchesOf(event: GestureResponderEvent, origin: ScreenPoint): readonly ScreenPoint[] {
  const touches = event.nativeEvent.touches;
  const listed = touches.length > 0 ? touches : [event.nativeEvent];
  return listed.map((touch) => ({ x: touch.pageX - origin.x, y: touch.pageY - origin.y }));
}

function sameView(a: RadarView, b: RadarView): boolean {
  return a.widthKm === b.widthKm && a.centre.x === b.centre.x && a.centre.y === b.centre.y;
}

const s = StyleSheet.create({
  field: { flex: 1, overflow: 'hidden' },
  anchor: { position: 'absolute', width: 0, height: 0, overflow: 'visible' },
  cardAt: { position: 'absolute', left: 0, top: 0 },
});
