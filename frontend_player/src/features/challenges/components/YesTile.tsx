/**
 * **A tile is a face** — the one the app already draws, at this screen's sizes, with two
 * additions ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3).
 *
 * `PlayerPhoto`'s `face` box, which is what a court seat draws: the photograph when the app has
 * one and the generated poster otherwise, at a corner that is a third of the box — which is what
 * the mocks' tiles measure at both sizes, so no second radius exists. What this screen adds:
 *
 * - **Two initials over a poster, and never over a photograph.** The poster is a fact about an
 *   id and the gradient alone cannot say who at tile size; a photograph already names the
 *   person, and letters over it would cover the one thing that does. The cut is
 *   `handleInitials`, beside `handleStem`, and it is a **drawing**: hidden from the screen
 *   reader with the rest of the tile, because the sentence that names everybody is the
 *   screen's header, built from whole handles. The day the initials are spoken, §3's fence
 *   has fallen.
 * - **An outlined empty seat** — the same box, a hairline in the on-dark colour, nothing in
 *   it. A seat still deciding, declined, lapsed, left or never filled is this (the room's own
 *   membership rule), and the sentence says *an empty seat* for it.
 *
 * The initials are set at a **share** of the tile (`size.yesTile.initials`) for the radius's
 * reason: two sizes of one drawn object, and a point per size is two numbers to keep in step.
 * It is the one font size in the app computed from a box, and it is computed here, in the tile
 * that owns the box.
 */

import { StyleSheet, Text, View } from 'react-native';

import { handleInitials } from '@/shared/formatting/playerName';
import { PlayerPhoto, playerPhotoRadius, theme } from '@/shared/ui';

import type { YesSeat } from '../domain/yesScreen';

export interface YesTileProps {
  readonly seat: YesSeat;
  /** `size.yesTile.singles` or `.doubles` — the screen decides which, off the court's length. */
  readonly size: number;
}

export function YesTile({ seat, size }: YesTileProps) {
  const box = { width: size, height: size, borderRadius: playerPhotoRadius(size) };

  if (seat.kind === 'empty') {
    return <View style={[box, s.empty]} testID="yes-tile-empty" />;
  }

  return (
    <View style={box} testID={seat.photoUrl === undefined ? 'yes-tile-poster' : 'yes-tile-photo'}>
      <PlayerPhoto
        playerId={seat.playerId}
        {...(seat.photoUrl === undefined ? {} : { photoUrl: seat.photoUrl })}
        box={{ kind: 'face', size }}
      />
      {/* Over the poster only. A seat whose handle the record has lost draws the poster bare:
          initials for `?` would be a drawing of nothing. */}
      {seat.photoUrl === undefined && seat.name !== undefined ? (
        <View
          style={s.initials}
          pointerEvents="none"
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          {/* Dynamic Type grows the letters and the box does not grow with them, so past the
              box they shrink back to fit — Part 13's own mechanism for a fixed box, never
              `allowFontScaling={false}`, which is the level bar's alone. */}
          <Text
            style={[s.letters, { fontSize: size * theme.size.yesTile.initials }]}
            numberOfLines={1}
            adjustsFontSizeToFit
          >
            {handleInitials(seat.name)}
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  empty: { borderWidth: 1, borderColor: theme.color.onDarkHair },
  initials: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center' },
  // White over the poster's light stop is 4,5:1 by the poster's own bound (2.5); the shadow is
  // the one every label over generated media carries.
  letters: {
    fontFamily: theme.font.sans[800],
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
});
