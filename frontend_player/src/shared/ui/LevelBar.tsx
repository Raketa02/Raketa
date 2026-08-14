/**
 * The level bar, per design-system 7.5 — **not a styled component but a drawn object**,
 * built from Views, with fixed geometry (`theme.size.levelBar`).
 *
 * ```
 * row 1   (y 0,  h 6)    four band segments, radius 3, the current band at full opacity
 *                        and the others at .38, 1pt separators in the surface colour
 * mark    (y −3, h 12)   3pt coral bar with a 2pt surface-coloured ring
 * row 2   (y 13, h 8)    the likely-range bracket: 2pt centre line with 2pt end caps
 * row 3   (y 24)         four band names — the current one at 800 in its band ink
 * legend  (optional)     a coral tick and a bracket glyph, with labels
 * ```
 *
 * **The separation of the two rows is the whole design.** An earlier version drew the
 * range on top of the bands and it hid exactly what the bands were there to show.
 *
 * **The scale is always the full 1,00–5,00**, so the same value lands in the same place on
 * the result screen, the passport and a comparison card alike.
 *
 * Three things worth knowing before changing it:
 *
 * - **The segment boundaries here are the theme's *drawing* values and are contiguous.
 *   They are not the model's band edges and must never be printed** (correction #4). The
 *   edges a screen prints come from the response; this component prints none.
 * - **Which band is the player's arrives as a key, never as a comparison.** Deriving it
 *   from `level` against these drawing boundaries would be a second opinion about banding,
 *   and the two would eventually disagree — which is the defect correction #4 records.
 * - **The separator and the mark's ring are both "the surface colour", and on a dark card
 *   that is the card.** Both exist to let the surface show through — one as a gap between
 *   segments, one as a cut-out around the mark — so `surface` on paper and `night` inside
 *   a dark card are the same instruction, not two.
 *
 * `variant="onDark"` is 5.2's repaint, and it is not optional decoration: `muted` and the
 * band `ink` values are computed against **paper** and fall to roughly 1,6:1 and 2,4:1 on
 * `night`, which Part 13 does not permit at any size. So on a dark card the bracket and the
 * unselected names take `onDarkTiny` and the current name takes plain white — **not the
 * band's `tint`**, which belongs to the bar and never to text. Band identity is carried
 * there by the segment, which is drawn in `deep` as always, and the current name is still
 * weight 800 against 600. Nothing about the state rests on colour either way.
 *
 * `allowFontScaling={false}` on the labels is the one place Part 13 permits it: a scaled
 * label breaks its alignment with the segment it names, and the alignment is the meaning.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme, type BandKey } from './theme';

const BANDS: readonly BandKey[] = ['new', 'developing', 'established', 'advanced'];

/** The drawn scale, and the only place it is written down. */
const SCALE_LOW = 1;
const SCALE_HIGH = 5;

export type LevelBarVariant = 'base' | 'onDark';

export interface LevelBarLegend {
  /** What the coral mark is — "Your level". */
  readonly mark: string;
  /** What the bracket is — "Likely range". */
  readonly bracket: string;
}

export interface LevelBarProps {
  readonly level: number;
  readonly range: { readonly low: number; readonly high: number };
  /**
   * The player's band. `undefined` where this build cannot name the band the response
   * sent: every segment then draws inactive and the mark still says where they are, which
   * is better than a bar that highlights the wrong one.
   */
  readonly band: BandKey | undefined;
  /** The four names, from the feature — this component holds no domain vocabulary. */
  readonly bandNames: Readonly<Record<BandKey, string>>;
  readonly variant?: LevelBarVariant;
  readonly legend?: LevelBarLegend;
  /** The bar is one element to a screen reader; this is what it says. */
  readonly accessibilityLabel: string;
}

export function LevelBar({
  level,
  range,
  band,
  bandNames,
  variant = 'base',
  legend,
  accessibilityLabel,
}: LevelBarProps) {
  const paint = PAINT[variant];

  return (
    <View accessible accessibilityLabel={accessibilityLabel}>
      <View style={s.track}>
        {BANDS.map((key, index) => {
          const draw = theme.band[key];
          const current = key === band;
          return (
            <View
              key={key}
              style={[
                s.segment,
                {
                  left: percent(fraction(draw.lo)),
                  width: percent(fraction(draw.hi) - fraction(draw.lo)),
                  backgroundColor: current ? draw.deep : draw.tint,
                  opacity: current ? 1 : bar.inactiveOpacity,
                  // The separator: the surface, showing through between two segments.
                  borderRightWidth: index === BANDS.length - 1 ? 0 : bar.segmentSeparator,
                  borderRightColor: paint.surface,
                },
              ]}
            />
          );
        })}

        <View
          style={[s.mark, { left: percent(fraction(level)), borderColor: paint.surface }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      </View>

      <View style={s.bracketRow}>
        <View
          style={[
            s.bracketLine,
            {
              left: percent(fraction(range.low)),
              width: percent(fraction(range.high) - fraction(range.low)),
              backgroundColor: paint.bracket,
            },
          ]}
        />
        <View
          style={[
            s.bracketCap,
            { left: percent(fraction(range.low)), backgroundColor: paint.bracket },
          ]}
        />
        <View
          style={[
            s.bracketCap,
            { left: percent(fraction(range.high)), backgroundColor: paint.bracket },
          ]}
        />
      </View>

      <View style={s.names}>
        {BANDS.map((key) => {
          const draw = theme.band[key];
          const current = key === band;
          return (
            <Text
              key={key}
              allowFontScaling={false}
              numberOfLines={1}
              style={[
                s.name,
                current ? s.nameCurrent : undefined,
                {
                  flexGrow: draw.hi - draw.lo,
                  color: current ? paint.bandName(key) : paint.bracket,
                },
              ]}
            >
              {bandNames[key]}
            </Text>
          );
        })}
      </View>

      {legend !== undefined ? (
        <View style={s.legend}>
          <View style={s.legendItem}>
            <View style={s.legendMark} />
            <Text allowFontScaling={false} style={[s.legendLabel, { color: paint.bracket }]}>
              {legend.mark}
            </Text>
          </View>
          <View style={s.legendItem}>
            <View style={s.legendBracket}>
              <View style={[s.legendBracketCap, { backgroundColor: paint.bracket }]} />
              <View style={[s.legendBracketLine, { backgroundColor: paint.bracket }]} />
              <View style={[s.legendBracketCap, { backgroundColor: paint.bracket }]} />
            </View>
            <Text allowFontScaling={false} style={[s.legendLabel, { color: paint.bracket }]}>
              {legend.bracket}
            </Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}

/** Where a level sits on the drawn scale, as a fraction of the bar's width. */
function fraction(value: number): number {
  const held = Math.min(Math.max(value, SCALE_LOW), SCALE_HIGH);
  return (held - SCALE_LOW) / (SCALE_HIGH - SCALE_LOW);
}

function percent(value: number): `${number}%` {
  return `${value * 100}%`;
}

const bar = theme.size.levelBar;

/** 5.2's repaint, expressed as the three colours that change with the surface. */
const PAINT: Readonly<
  Record<LevelBarVariant, { surface: string; bracket: string; bandName: (key: BandKey) => string }>
> = {
  base: {
    surface: theme.color.surface,
    bracket: theme.color.muted,
    bandName: (key) => theme.band[key].ink,
  },
  onDark: {
    surface: theme.color.night,
    bracket: theme.color.onDarkTiny,
    bandName: () => theme.color.surface,
  },
};

const s = StyleSheet.create({
  // The mark overhangs the track by 3pt at the top, so the row starts 3pt lower and
  // nothing above it is clipped.
  track: { height: bar.trackHeight, marginTop: -bar.markTop },
  segment: {
    position: 'absolute',
    top: bar.trackTop,
    height: bar.trackHeight,
    borderRadius: bar.trackRadius,
  },
  mark: {
    position: 'absolute',
    top: bar.markTop,
    width: bar.markWidth + 2 * bar.markRing,
    height: bar.markHeight,
    // Centred on its value rather than started at it.
    marginLeft: -(bar.markWidth / 2 + bar.markRing),
    backgroundColor: theme.color.coral,
    borderWidth: bar.markRing,
    borderRadius: bar.markRing,
  },
  bracketRow: {
    height: bar.bracketHeight,
    marginTop: bar.bracketTop - (bar.trackTop + bar.trackHeight),
  },
  bracketLine: {
    position: 'absolute',
    top: (bar.bracketHeight - bar.bracketStroke) / 2,
    height: bar.bracketStroke,
  },
  bracketCap: {
    position: 'absolute',
    top: 0,
    width: bar.bracketStroke,
    height: bar.bracketHeight,
    marginLeft: -bar.bracketStroke / 2,
  },
  names: {
    flexDirection: 'row',
    marginTop: bar.namesTop - (bar.bracketTop + bar.bracketHeight),
  },
  // 7.5 gives the names weights (800 current, 600 otherwise) but no size; `tag` is the
  // 9.5pt role, and on Android the family is what carries weight.
  name: {
    ...theme.type.tag,
    fontFamily: theme.font.sans[600],
    flexBasis: 0,
    textAlign: 'center',
  },
  nameCurrent: { fontFamily: theme.font.sans[800] },
  legend: { flexDirection: 'row', gap: theme.space.md, marginTop: theme.space.xs },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  legendMark: {
    width: bar.markWidth,
    height: bar.markHeight - 2 * bar.markRing,
    backgroundColor: theme.color.coral,
  },
  legendBracket: { flexDirection: 'row', alignItems: 'center' },
  legendBracketCap: { width: bar.bracketStroke, height: bar.bracketHeight },
  legendBracketLine: { width: theme.space.sm, height: bar.bracketStroke },
  legendLabel: { ...theme.type.tag, fontFamily: theme.font.sans[600] },
});
