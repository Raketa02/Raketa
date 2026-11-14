/**
 * **The tinted pale tile** — a light card washed from its top-left in the colour of the player's
 * court poster, the colour that never changes for them
 * ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows screens §6.2, §11; home rows
 * 20, 22–22.3, 24; design-system 7.35). Same vibe draws it on Home's row and in See all's two columns.
 *
 * ```
 * ┌─────────────────────────────┐
 * │▓▓▒▒░░                       │   ← the poster's hue at TINTED_TILE.tint, from the top-left corner …
 * │▒▒░░   the caller's words    │
 * │░░                           │   ← … gone by TINTED_TILE.until of the diagonal: surface beneath
 * │                         (✓) │   ← bottom-right, a control of its own: the corner's 44 kept clear
 * └─────────────────────────────┘
 * ```
 *
 * ## The tint is the poster's hue, so it is the same person everywhere
 *
 * **`courtPosterFor`'s hue, its light stop** — the one a player with no photograph wears as their
 * face — laid over `surface` at an eighth at most, so the tile is a pale card and every word on it
 * reads as on a card (`tintedTile.test.ts` derives `muted` on the strongest corner of all sixteen
 * hues). **The hue is still never read**: it names no sport (the poster's 25° bound) and says nothing
 * about the person; it is the same colour their poster is, which is all it is for. No colour is
 * written here — the sixteen are the theme's, and this file takes one as the poster does.
 *
 * ## Two doors
 *
 * **The tile opens; the corner acts.** The corner is a sibling laid over the tile's foot, never inside
 * its press — the round friend button sends a request, and a tap anywhere else opens the caller's
 * sheet — as `PortraitTile` draws its corner. The tile keeps the corner's 44 clear under the words, so
 * nothing the caller draws stands under the button.
 *
 * ## Its width is the caller's
 *
 * Home's rail hands its card width; See all hands its column. The height is the words', and a rail or
 * a grid line stretches its tiles to the tallest. Pressed, the words dim to 6.6's `.7`; the tint stays.
 */

import { useId, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { courtPosterFor } from './courtPosterFraming';
import { theme } from './theme';

/**
 * **The wash** — the poster hue's strength at the top-left corner, and the share of the diagonal by
 * which it has gone. MEASURED off home rows 22 at 1× (the green poster's corner, `#EAF3E6` over white,
 * is its hue at about a tenth), and held where `muted` keeps 4,5 on the strongest corner of every hue:
 * 4,62 at 0,12, and exactly 4,50 at 0,14 — so this is a ceiling, not a taste (`tintedTile.test.ts`).
 */
export const TINTED_TILE = { tint: 0.12, until: 0.7 } as const;

export interface TintedTileProps {
  /** Whose poster's hue tints the tile — the poster's own input. */
  readonly playerId: string;
  /** **The tile's spoken name** — who, and what the words over it say. */
  readonly accessibilityLabel: string;
  /** What the tile's own press does. */
  readonly onPress: () => void;
  /** Bottom-right: **a control of its own**, beside the tile's press — the round friend button. */
  readonly corner?: ReactNode;
  /** Home's row: the rail's card width. See all: the column's. Absent, the width it is given. */
  readonly width?: number;
  readonly testID?: string;
  readonly children: ReactNode;
}

export function TintedTile({
  playerId,
  accessibilityLabel,
  onPress,
  corner,
  width,
  testID,
  children,
}: TintedTileProps) {
  return (
    <View
      style={[s.tile, width === undefined ? undefined : { width }]}
      {...(testID === undefined ? {} : { testID })}
    >
      <Tint playerId={playerId} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        onPress={onPress}
        style={({ pressed }) => [s.press, pressed ? s.pressed : undefined]}
      >
        {children}
        {corner === undefined ? null : <View style={s.cornerRoom} />}
      </Pressable>
      {corner === undefined ? null : <View style={s.corner}>{corner}</View>}
    </View>
  );
}

/** The wash — drawn, and hidden: it is the ground the words stand on, not a thing. */
function Tint({ playerId }: { readonly playerId: string }) {
  const gradient = useId();
  const hue = courtPosterFor(playerId).hue.light;
  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      testID="tinted-tile-tint"
    >
      <Svg width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">
        <Defs>
          <LinearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
            <Stop offset={0} stopColor={hue} stopOpacity={TINTED_TILE.tint} />
            <Stop offset={TINTED_TILE.until} stopColor={hue} stopOpacity={0} />
          </LinearGradient>
        </Defs>
        <Rect x={0} y={0} width={1} height={1} fill={`url(#${gradient})`} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  // 5.1's light card — surface, a `line` border, radius.card — clipping its wash. No shadow.
  tile: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
  },
  press: { flexGrow: 1, paddingHorizontal: theme.space.md, paddingTop: theme.space.md },
  // 6.6: the words dim; the ground does not.
  pressed: { opacity: 0.7 },
  // The corner's own 44 under the words, so nothing stands under the button.
  cornerRoom: { height: theme.size.minTouch },
  // At the very corner: the control brings its own 44pt reach (the round button's circle sits 10 in),
  // and a reach past the tile's edge would be clipped away with it.
  corner: { position: 'absolute', right: 0, bottom: 0 },
});
