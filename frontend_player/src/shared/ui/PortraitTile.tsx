/**
 * **The portrait tile** — a player's face edge to edge, a wash rising over its foot, and the words
 * over the wash ([#801](https://github.com/Rakieta02/Rakieta/issues/801); the Home rows screens §5.2,
 * §11; home rows 17–19; design-system 7.31). New in Rakieta draws it on Home's row and in See all's
 * two columns; Top 10's card draws it too (#805).
 *
 * ```
 * ┌──────────────────────┐
 * │ [NEW]            (+) │   ← the tag top-left (`tag`), a control top-right (`corner`)
 * │                      │
 * │     photo / poster   │   ← PlayerPhoto's media, edge to edge
 * │░░░░░░░░░░░░░░░░░░░░░░│   ← the wash: nothing at 40 % of the height …
 * │ bartek.l             │
 * │ ● Padel 2,35         │   ← the words (`children`), over it
 * │ Joined 2 days ago    │   ← … `portraitWash` from 70 %, held to the foot
 * └──────────────────────┘
 * ```
 *
 * ## Two doors
 *
 * **The tile opens; the corner acts.** The corner is a sibling laid over the tile, never inside its
 * press, so a tap on the round friend button sends a request and a tap anywhere else opens the
 * record — two controls, as Home's group card draws its chip beside its own press (7.30). The tag is
 * a picture, not a control, and lets every touch through to the tile.
 *
 * ## The wash, and what is legible on it
 *
 * **The deck card's wash, which this tile now wears alone** (`theme.color.portraitWash`, Part 16
 * 2026-11-14): a linear ramp in the tile's own box from nothing at `WASH_FROM` of its height to `ink`
 * at .94 at `WASH_FULL`, held to the foot. The words stand from about 60 % of the height down (home
 * rows 18: the name's top edge at 330 of 556 pixels), where the ramp is already at about two thirds
 * of its strength, `ink` at about .63 — the photo panel's flat pin within a step — and everything
 * under the name sits deeper on it. Every label over it carries `textOnMedia`, as on the deck card,
 * because a photograph can be anything. **Not seen on a device**: legibility over a pale photograph
 * at the name is the author's to check against the mocks.
 *
 * ## Its size is the caller's
 *
 * **A width and an aspect, handed in**: Home's row hands the rail's tile width and 11:8, See all its
 * column and 9:8 (`theme.size.portraitTile`). The corner is 15 — a dark card's, the surface this is
 * the nearest of (4.2: bigger surface, rounder; a tile is smaller than a card and darker than one).
 * Pressed, the tile dims to 6.6's `.7`, the photo tile's own press.
 */

import { useId, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { PlayerPhoto } from './PlayerPhoto';
import { theme } from './theme';

/** Where the wash starts, and where it is whole — shares of the tile's height (the module note). */
const WASH_FROM = 0.4;
const WASH_FULL = 0.7;

export interface PortraitTileProps {
  /** Whose face — the poster's whole input where there is no photograph. */
  readonly playerId: string;
  /** Their first photograph; absent draws the poster. */
  readonly photoUrl?: string;
  readonly width: number;
  /** Height over width — `theme.size.portraitTile`'s `railAspect` or `gridAspect`. */
  readonly aspect: number;
  /** **The tile's spoken name** — who, and the lines drawn over the wash. */
  readonly accessibilityLabel: string;
  /** What the tile's own press does — opens the record. */
  readonly onPress: () => void;
  /** Top-left over the face: a picture that lets touches through — New in Rakieta's *NEW*. */
  readonly tag?: ReactNode;
  /** Top-right: **a control of its own**, beside the tile's press — the round friend button. */
  readonly corner?: ReactNode;
  readonly testID?: string;
  /** The words over the wash, at the foot. */
  readonly children: ReactNode;
}

export function PortraitTile({
  playerId,
  photoUrl,
  width,
  aspect,
  accessibilityLabel,
  onPress,
  tag,
  corner,
  testID,
  children,
}: PortraitTileProps) {
  return (
    <View
      style={[s.tile, { width, height: width * aspect }]}
      {...(testID === undefined ? {} : { testID })}
    >
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        onPress={onPress}
        style={({ pressed }) => [StyleSheet.absoluteFill, pressed ? s.pressed : undefined]}
      >
        <View style={StyleSheet.absoluteFill}>
          <PlayerPhoto
            playerId={playerId}
            {...(photoUrl === undefined ? {} : { photoUrl })}
            box={{ kind: 'media' }}
          />
        </View>
        <Wash />
        <View style={s.foot}>{children}</View>
      </Pressable>
      {tag === undefined ? null : (
        <View style={s.tag} pointerEvents="none">
          {tag}
        </View>
      )}
      {corner === undefined ? null : <View style={s.corner}>{corner}</View>}
    </View>
  );
}

/** The ramp — drawn, and hidden: it is the ground the words stand on, not a thing. */
function Wash() {
  const gradient = useId();
  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      testID="portrait-wash"
    >
      <Svg width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">
        <Defs>
          <LinearGradient id={gradient} x1="0" y1="0" x2="0" y2="1">
            <Stop offset={WASH_FROM} stopColor={theme.color.portraitWash} stopOpacity={0} />
            <Stop offset={WASH_FULL} stopColor={theme.color.portraitWash} stopOpacity={1} />
            <Stop offset={1} stopColor={theme.color.portraitWash} stopOpacity={1} />
          </LinearGradient>
        </Defs>
        <Rect x={0} y={0} width={1} height={1} fill={`url(#${gradient})`} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  tile: {
    borderRadius: theme.radius.cardDark,
    overflow: 'hidden',
    backgroundColor: theme.color.night,
  },
  // 6.6: the photo tile's press.
  pressed: { opacity: 0.7 },
  foot: {
    position: 'absolute',
    left: theme.space.sm,
    right: theme.space.sm,
    bottom: theme.space.sm,
    gap: theme.space.xxs,
  },
  tag: { position: 'absolute', top: theme.space.sm, left: theme.space.sm },
  // At the very corner: the control brings its own 44pt reach (the round button's circle sits 10 in,
  // beside the tag's 9), and a reach past the tile's edge would be clipped away with it.
  corner: { position: 'absolute', top: 0, right: 0 },
});
