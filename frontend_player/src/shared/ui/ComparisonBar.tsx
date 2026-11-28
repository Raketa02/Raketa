/**
 * **The comparison bar** — two players' levels in one sport on the Skill passport's scale, per
 * design-system 7.33 ([#802](https://github.com/Rakieta02/Rakieta/issues/802); the Home rows screens
 * §4.2–§4.3; home rows 7–16). A drawn object, like 7.5's level bar, and **reading that bar's scale and
 * bands, never new ones** (`levelScaleFraction`, `LEVEL_BANDS`, `theme.band`).
 *
 * ```
 * label   YOU, centred over the mark, labelGap above the row
 * row     (h 22)  the track, 8 high and centred in the row: four band segments, each its tint
 *                 (onDark: at onDarkBand over the ground · base: at 7.5's inactiveOpacity), 1pt
 *                 separators in the surface; the fill from the left to THEIR level (onDark volt ·
 *                 base mint); the mark at YOURS, 6 wide and 22 tall in a 2pt ring of the surface
 *                 (onDark white · base ink)
 * names   namesTop under the row — the four band names, uppercase, each as wide as its band; the
 *         reader's own at 800, the rest at 600
 * ```
 *
 * **A fill short of the mark means they are below the reader, one past it above** (home rows 7, 8):
 * the bar is the gap drawn, and the card says it in words beside it.
 *
 * **Which band is the reader's arrives as a key**, from the band the rating published — never by
 * comparing a level with these drawing values, 7.5's correction #4.
 *
 * The bar is one element to a screen reader, named by the caller (its two levels); its parts are
 * hidden. `allowFontScaling={false}` on the labels for 7.5's reason: a scaled label leaves the
 * segment it names.
 */

import { StyleSheet, Text, View } from 'react-native';

import { LEVEL_BANDS, levelScaleFraction } from './LevelBar';
import { theme, type BandKey } from './theme';

export type ComparisonBarVariant = 'onDark' | 'base';

export interface ComparisonBarProps {
  /** The reader's level — the tall mark. */
  readonly yours: number;
  /** The other's level — where the fill ends. */
  readonly theirs: number;
  /** The reader's band, bold under the bar — `undefined` where this build cannot name it. */
  readonly band: BandKey | undefined;
  /** The four names, from the feature — this component holds no domain vocabulary. */
  readonly bandNames: Readonly<Record<BandKey, string>>;
  /** The mark's label — *YOU*. */
  readonly markLabel: string;
  /** `onDark` on the Same level card's ground; `base` on a sheet. */
  readonly variant: ComparisonBarVariant;
  /** The bar is one element to a screen reader; this is what it says. */
  readonly accessibilityLabel: string;
}

export function ComparisonBar({
  yours,
  theirs,
  band,
  bandNames,
  markLabel,
  variant,
  accessibilityLabel,
}: ComparisonBarProps) {
  const paint = PAINT[variant];
  const mark = percent(levelScaleFraction(yours));

  return (
    <View
      accessible
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="image"
      testID="comparison-bar"
    >
      <View style={s.labelRow} importantForAccessibility="no-hide-descendants">
        <Text
          allowFontScaling={false}
          numberOfLines={1}
          style={[s.label, { left: mark, color: paint.label }]}
          accessibilityElementsHidden
        >
          {markLabel}
        </Text>
      </View>

      <View
        style={s.row}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <View style={s.track}>
          {LEVEL_BANDS.map((key, index) => {
            const draw = theme.band[key];
            return (
              <View
                key={key}
                style={[
                  s.segment,
                  {
                    left: percent(levelScaleFraction(draw.lo)),
                    width: percent(levelScaleFraction(draw.hi) - levelScaleFraction(draw.lo)),
                    backgroundColor: draw.tint,
                    opacity: paint.bandOpacity,
                  },
                  index === LEVEL_BANDS.length - 1 ? undefined : s.separated,
                  { borderRightColor: paint.surface },
                ]}
              />
            );
          })}
          <View
            testID="comparison-fill"
            style={[
              s.fill,
              { width: percent(levelScaleFraction(theirs)), backgroundColor: paint.fill },
            ]}
          />
        </View>
        <View
          testID="comparison-mark"
          style={[s.mark, { left: mark, backgroundColor: paint.mark, borderColor: paint.surface }]}
        />
      </View>

      <View
        style={s.names}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        {LEVEL_BANDS.map((key) => {
          const draw = theme.band[key];
          const current = key === band;
          return (
            <Text
              key={key}
              allowFontScaling={false}
              numberOfLines={1}
              adjustsFontSizeToFit
              minimumFontScale={bar.nameMinScale}
              style={[
                s.name,
                current ? s.nameCurrent : undefined,
                {
                  flexGrow: draw.hi - draw.lo,
                  color: current ? paint.current : paint.name,
                },
              ]}
            >
              {bandNames[key]}
            </Text>
          );
        })}
      </View>
    </View>
  );
}

function percent(value: number): `${number}%` {
  return `${value * 100}%`;
}

const bar = theme.size.comparisonBar;

/** The two paints — every colour that changes with the surface the bar stands on. */
const PAINT: Readonly<
  Record<
    ComparisonBarVariant,
    {
      readonly surface: string;
      readonly bandOpacity: number;
      readonly fill: string;
      readonly mark: string;
      readonly label: string;
      readonly name: string;
      readonly current: string;
    }
  >
> = {
  onDark: {
    surface: theme.color.levelCardGround,
    bandOpacity: bar.onDarkBand,
    fill: theme.color.volt,
    mark: theme.color.surface,
    label: theme.color.surface,
    name: theme.color.onDarkTiny,
    current: theme.color.surface,
  },
  base: {
    surface: theme.color.surface,
    bandOpacity: theme.size.levelBar.inactiveOpacity,
    fill: theme.color.mint,
    mark: theme.color.ink,
    label: theme.color.ink,
    name: theme.color.muted,
    current: theme.color.ink,
  },
};

/** The label's box, centred on the mark — wider than *YOU* at any font the app loads. */
const LABEL_BOX = 4 * theme.space.md;

const s = StyleSheet.create({
  labelRow: { height: theme.type.tag.lineHeight, marginBottom: bar.labelGap },
  label: {
    ...theme.type.tag,
    fontFamily: theme.font.sans[800],
    position: 'absolute',
    width: LABEL_BOX,
    marginLeft: -LABEL_BOX / 2,
    textAlign: 'center',
  },
  row: { height: bar.markHeight, justifyContent: 'center' },
  track: {
    height: bar.trackHeight,
    borderRadius: bar.trackHeight / 2,
    overflow: 'hidden',
  },
  segment: { position: 'absolute', top: 0, bottom: 0 },
  separated: { borderRightWidth: theme.size.levelBar.segmentSeparator },
  fill: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    borderRadius: bar.trackHeight / 2,
  },
  mark: {
    position: 'absolute',
    top: 0,
    width: bar.markWidth + 2 * bar.markRing,
    height: bar.markHeight,
    // Centred on its value rather than started at it.
    marginLeft: -(bar.markWidth / 2 + bar.markRing),
    borderWidth: bar.markRing,
    borderRadius: (bar.markWidth + 2 * bar.markRing) / 2,
  },
  names: { flexDirection: 'row', marginTop: bar.namesTop },
  // 7.5's names, set as the mocks set them: uppercase at `tag`'s size.
  name: {
    ...theme.type.tag,
    fontFamily: theme.font.sans[600],
    flexBasis: 0,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  nameCurrent: { fontFamily: theme.font.sans[800] },
});
