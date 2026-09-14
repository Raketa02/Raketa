/**
 * The court — [7.12](../../../docs/design-system.md#712-the-court), and the fifth drawn
 * object.
 *
 * ```
 * ground   a 150 gradient from the Sport hue to `night`, under one `courtScrim` pass
 * chrome   one white at four weights — the boundary, the net, the inner lines, the wall
 * caption  eyebrow, over a gradient to `courtScrim`, with `textOnMedia`
 * seats    positions only. The caller supplies what stands in each one.
 * ```
 *
 * **It takes a Sport and a box, draws the ground and the seat *positions*, and takes
 * children in seat order.** Two other shapes were refused and both fail the same way. A
 * `renderSeat(index, position)` callback is this with an indirection. A
 * `useCourtGeometry(sport, width)` hook **returns** the coordinates, and geometry that is
 * returned is geometry that gets adjusted at one call site and not the other — which is the
 * drift `src/shared/ui/README.md` exists to prevent, arriving through the door the folder
 * rule was written to close. With children the positions never leave this module, and the
 * interface is testable through itself: hand it two children, assert two positions, per
 * Sport.
 *
 * **The seat coordinates cannot be derived, and H-25 is why.** Squash has no net: both
 * players stand on the same half, so *seat 3* is not where seat 3 is in padel, and reflecting
 * the near side about the middle produces the wrong court for one Sport in four. They are
 * `theme.size.court.seats`, per Sport, in seat order — your side first.
 *
 * **The read-only court and the interactive one are not a flag on this component.** They
 * share every number and no behaviour, so they are two feature components over one drawn
 * object: read-only faces and pressable seats are *different children*.
 *
 * **This file holds no copy.** The caption, the two side labels and the summary a screen
 * reader hears first all arrive as props, because the pool header and the forecast card do
 * not say the same things about the same court.
 */

import { Children, useId, type ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Defs, LinearGradient, Path, Rect, Stop } from 'react-native-svg';

import { theme, type SportKey } from './theme';

const court = theme.size.court;
const SPACE = court.space;
const LINE = court.line;

/**
 * The four line-sets, in the drawing's own units.
 *
 * Vector path data, copied across rather than derived — a court's markings are a fact about
 * the sport, and the specification's own self-check says so. What is *not* copied is the
 * weights: the prototype drew padel's inner lines at `.28` and the other three at `.24`, and
 * one line weight across four courts is the whole reason this is one component.
 *
 * **Padel's second boundary pass — a 5pt white at `.12`, the glass wall — is dropped**, on
 * [6.9](../../../docs/design-system.md#69-the-photo-tile-and-picker)'s argument for dropping
 * the poster's: it is a mark lighter than the ground it sits on, drawn over the court's own
 * boundary, and the boundary is already there.
 *
 * **Squash's out-line takes the net's weight and none of its glow.** The glow is a net's
 * depth, and squash has no net; the line across the front wall is still the line the game is
 * played against, so it is drawn as heavily.
 */
/** A rectangle in the drawing's units. Both marks that are one are the same four numbers. */
interface Box {
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
  readonly rx?: number;
}

/** Those four, as `Rect` spells them. Written once so two marks cannot disagree about them. */
const box = ({ x, y, w, h, rx }: Box) => ({ x, y, width: w, height: h, rx });

interface LineSet {
  readonly bound: Box;
  /** The full-width line the game is played across, and whether it is a net. */
  readonly across?: { readonly d: string; readonly glow: boolean };
  /** Squash's front wall — a band, and the only filled mark on any court. */
  readonly wall?: Box;
  readonly inner: string;
}

const LINES: Readonly<Record<SportKey, LineSet>> = {
  padel: {
    bound: { x: 6, y: 6, w: 88, h: 120, rx: 2 },
    across: { d: 'M6,66 H94', glow: true },
    inner: 'M14,30 H86 M14,102 H86 M50,30 V6 M50,102 V126',
  },
  badminton: {
    bound: { x: 8, y: 6, w: 84, h: 120 },
    across: { d: 'M8,66 H92', glow: true },
    inner: 'M8,42 H92 M8,90 H92 M50,6 V42 M50,90 V126 M14,6 V126 M86,6 V126',
  },
  tennis: {
    bound: { x: 8, y: 6, w: 84, h: 120 },
    across: { d: 'M8,66 H92', glow: true },
    inner: 'M16,6 V126 M84,6 V126 M16,36 H84 M16,96 H84 M50,36 V96',
  },
  squash: {
    bound: { x: 8, y: 6, w: 84, h: 120 },
    across: { d: 'M8,22 H92', glow: false },
    wall: { x: 8, y: 6, w: 84, h: 16 },
    inner: 'M8,80 H92 M50,80 V126 M8,96 H30 M70,96 H92 M30,80 V96 M70,80 V96',
  },
};

/** How many people stand on a court of each Sport. Read off the seats, never restated. */
export function courtSeatCount(sport: SportKey): number {
  return court.seats[sport].length;
}

/** The face a seat is drawn at, against the court's width, with a floor: below it, a dot. */
export function courtSeatSize(width: number): number {
  return Math.max(court.seatMin, Math.round(width * court.seatRatio));
}

export interface CourtProps {
  readonly sport: SportKey;
  /** The court's width. Its height is the drawing's own 1,32 — never given separately. */
  readonly width: number;
  /**
   * One accessibility element **preceding** the seats: `{Sport}, {n} of {m} seats filled.`
   * Four seats announced against nothing are four seats a listener cannot place
   * (`the-words.md` 20.4). The sentence is the caller's; that it comes first is not.
   */
  readonly summary: string;
  /** Bottom strip. Drawn, never announced — the summary already names the Sport. */
  readonly caption?: string;
  /** Your side, then theirs. Drawn, never announced — each seat names its own side. */
  readonly sideLabels?: readonly [string, string];
  /**
   * In seat order. The court places them; it never asks what they are.
   *
   * **Every seat is a child, including an empty one.** An empty seat is a real element with a
   * sentence of its own (`the-words.md` §20.4: `{side}, empty`), so a hole in this list is
   * never the right way to express one — and a `null` among the children shifts every seat
   * after it, which the court cannot see and cannot warn about.
   */
  readonly children?: ReactNode;
}

export function Court({ sport, width, summary, caption, sideLabels, children }: CourtProps) {
  // PER INSTANCE, never derived from the Sport or the width: the pool draws one court in its
  // header and another in a card, and an id composed from data emits duplicates the moment a
  // screen draws two of the same Sport — `CourtPoster` closed exactly this bug (UI G6 #3).
  const id = useId();
  const ground = `${id}-ground`;
  const captionBand = `${id}-caption`;
  const height = (width * SPACE.height) / SPACE.width;
  const seat = courtSeatSize(width);
  const lines = LINES[sport];
  const seats = court.seats[sport];

  return (
    <View style={[s.court, { width, height }]}>
      {/*
       * The summary, first in the tree and at the top edge, so a listener reaches it before
       * any seat. It is not the court's own `accessibilityLabel`: a container carrying one
       * would swallow the seats, which are the elements this screen is navigated by.
       *
       * A thin strip rather than a zero-size box — an element with no frame is one a screen
       * reader may skip — and the ground is drawn over it, so nothing of it is visible. It
       * sits above every seat on every Sport: the highest is at 22 of 132.
       */}
      <View accessible accessibilityLabel={summary} style={s.summary} />

      {/*
       * **The ground is clipped to its radius; the seats are not.** The clip used to sit on the
       * court itself, and it cropped what a seat hangs below its face: at `card` (88) the
       * near-right seat of a doubles court stands at 110 of 132, and the three letters under
       * it end six points past the court's bottom edge — drawn cut in half through the glyphs.
       * A seat is the caller's child and the court only places it, so nothing here decides
       * where its caption may end; the rounded corners are the ground's, and the ground is the
       * one layer that needs them.
       */}
      <View style={s.ground}>
        <Svg
          width={width}
          height={height}
          viewBox={`0 0 ${SPACE.width} ${SPACE.height}`}
          style={StyleSheet.absoluteFill}
        >
          <Defs>
            <LinearGradient id={ground} x1="0" y1="0" x2="0.5" y2="0.87">
              <Stop offset="0" stopColor={theme.sport[sport]} />
              <Stop offset="1" stopColor={theme.color.night} />
            </LinearGradient>
            <LinearGradient id={captionBand} x1="0" y1="0" x2="0" y2="1">
              <Stop offset="0" stopColor={theme.color.night} stopOpacity={0} />
              <Stop offset="1" stopColor={theme.color.courtScrim} />
            </LinearGradient>
          </Defs>

          {/* The hue, then one scrim pass over it. Pinned at .93, which is what makes 2.5's
              four ratios finite rather than one per Sport per screen. */}
          <Rect x={0} y={0} width={SPACE.width} height={SPACE.height} fill={`url(#${ground})`} />
          <Rect
            x={0}
            y={0}
            width={SPACE.width}
            height={SPACE.height}
            fill={theme.color.courtScrim}
          />

          {lines.wall === undefined ? null : (
            <Rect {...box(lines.wall)} fill={theme.color.surface} fillOpacity={LINE.wall} />
          )}

          <Rect
            {...box(lines.bound)}
            fill="none"
            stroke={theme.color.surface}
            strokeOpacity={LINE.bound}
            strokeWidth={LINE.boundWidth}
          />

          {lines.across === undefined ? null : (
            <>
              {lines.across.glow ? (
                <Path
                  d={lines.across.d}
                  stroke={theme.color.surface}
                  strokeOpacity={LINE.netGlow}
                  strokeWidth={LINE.netGlowWidth}
                />
              ) : null}
              <Path
                d={lines.across.d}
                stroke={theme.color.surface}
                strokeOpacity={LINE.net}
                strokeWidth={LINE.netWidth}
              />
            </>
          )}

          <Path
            d={lines.inner}
            fill="none"
            stroke={theme.color.surface}
            strokeOpacity={LINE.inner}
            strokeWidth={LINE.innerWidth}
          />

          {caption === undefined ? null : (
            <Rect
              x={0}
              y={SPACE.height - CAPTION_BAND}
              width={SPACE.width}
              height={CAPTION_BAND}
              fill={`url(#${captionBand})`}
            />
          )}
        </Svg>
      </View>

      {sideLabels === undefined ? null : (
        <View
          style={s.sides}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          {/* Theirs is the far half, so it is drawn first — the court reads down the page
              while a seat list reads up it, and this is the one place the two meet. */}
          <Text style={s.sideLabel}>{sideLabels[1]}</Text>
          <Text style={s.sideLabel}>{sideLabels[0]}</Text>
        </View>
      )}

      {/* Positions, not people. Each child is centred on its seat and fills the box it is
          given, so a face, an empty ring and a pressable seat are all the same geometry.

          `Children.toArray` rather than a cast: it flattens a fragment or a nested array,
          which a hand-rolled `Array.isArray` reads as one seat. The key is the INDEX because
          the wrapper is the seat's slot rather than its occupant — slot 2 stays slot 2 when
          the person in it changes, which is the whole point of a swap. */}
      {Children.toArray(children).map((child, index) => {
        const position = seats[index];
        if (position === undefined) return null;
        return (
          <View
            key={index}
            style={[
              s.seat,
              {
                width: seat,
                height: seat,
                left: (width * position[0]) / SPACE.width - seat / 2,
                top: (height * position[1]) / SPACE.height - seat / 2,
              },
            ]}
          >
            {child}
          </View>
        );
      })}

      {caption === undefined ? null : (
        <Text
          style={s.caption}
          numberOfLines={1}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          {caption}
        </Text>
      )}
    </View>
  );
}

/** The caption's gradient band, in drawing units — a fifth of the court's height. */
const CAPTION_BAND = SPACE.height / 5;

const s = StyleSheet.create({
  // The box: a width and its 1,32. It clips nothing — see the note at the ground.
  court: {},
  ground: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: theme.radius.court,
    overflow: 'hidden',
    // The ground is also the view's own fill, so a box still laying out shows the court's
    // dark end rather than the paper behind it — `CourtPoster`'s rule.
    backgroundColor: theme.color.night,
  },
  summary: { position: 'absolute', top: 0, left: 0, right: 0, height: theme.space.xxs },
  seat: { position: 'absolute' },
  sides: { ...StyleSheet.absoluteFillObject, justifyContent: 'space-between' },
  sideLabel: {
    ...theme.type.eyebrow,
    ...theme.shadow.textOnMedia,
    color: theme.color.surface,
    // 2.5's own recorded value: 5,46 against the worst of the four grounds, which already
    // clears AA — so it is not raised, and the figure is here so nobody raises it.
    opacity: court.sideLabelOpacity,
    textAlign: 'center',
    textTransform: 'uppercase',
    paddingVertical: theme.space.xxs,
  },
  caption: {
    ...theme.type.eyebrow,
    ...theme.shadow.textOnMedia,
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    color: theme.color.surface,
    textAlign: 'center',
    textTransform: 'uppercase',
    paddingVertical: theme.space.xxs,
    paddingHorizontal: theme.space.xs,
  },
});
