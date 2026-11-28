/**
 * **The photo carousel** — all of a player's photos, sideways, a card at a time
 * ([#799](https://github.com/Rakieta02/Rakieta/issues/799); the Home rows screens §6.3, §9.3; home rows
 * 23; Part 16, 2026-11-14).
 *
 * ```
 * ┌──────────────┐ ┌──────────────┐ ┌──    ← from the content's left edge, bleeding past the right
 * │              │ │              │ │      ← a card is photoCarouselRatio of the content width
 * │   photo 1    │ │   photo 2    │ │      ← 4:5, PHOTO_PANEL's own shape (7.16), radius.card
 * │              │ │              │ │
 * └──────────────┘ └──────────────┘ └──    ← Part 8's Strip: gap 9, snapping a card at a time
 * ```
 *
 * **Every photo is drawn**, in the order handed in, since any player's record opens with all of them
 * (ADR-0204 §2). **The record draws it first, and the vibe sheet draws the same one** — *the record
 * and the sheet draw one carousel*, the Home rows screens §9.3's call — so it is a drawn object here
 * rather than a feature's.
 *
 * **Nothing with no photo** (the screens §6.3's call): a carousel of posters would draw a stranger's
 * generated picture as if it were theirs, and the record's header already draws one where there is
 * no photograph. **A lone photo keeps the card's size** — a 4:5 card the content's width would stand
 * taller than the rest of the sheet's first screen.
 *
 * **It announces nothing**, as a face announces nothing (`PlayerPhoto`): a photograph of somebody is
 * not a fact this app describes, and nothing here is pressed. It sits in a sheet whose title and
 * header already say whose they are.
 *
 * **It never imports a feature.** The photos arrive as data; the URLs are the response's own,
 * short-lived and recorded nowhere.
 */

import { ScrollView, StyleSheet, View, useWindowDimensions } from 'react-native';

import { PHOTO_PANEL, PlayerPhoto } from './PlayerPhoto';
import { theme } from './theme';

/** One photo to draw — its id, which keys it, and the response's signed link. */
export interface CarouselPhoto {
  readonly photoId: string;
  readonly photoUrl: string;
}

export interface PhotoCarouselProps {
  /** Whose photos — the poster's input, should a link come back empty. */
  readonly playerId: string;
  /** **Every photo, in the player's order.** None draws nothing. */
  readonly photos: readonly CarouselPhoto[];
  readonly testID?: string;
}

export function PhotoCarousel({ playerId, photos, testID }: PhotoCarouselProps) {
  const { width: screen } = useWindowDimensions();
  if (photos.length === 0) return null;

  const content = screen - 2 * theme.size.gutter;
  const width = content * theme.size.photoCarouselRatio;
  const height = width * PHOTO_SHAPE;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      snapToInterval={width + STRIP_GAP}
      decelerationRate="fast"
      style={s.strip}
      contentContainerStyle={s.stripContent}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      {...(testID === undefined ? {} : { testID })}
    >
      {photos.map((photo) => (
        <View
          key={photo.photoId}
          testID={`carousel-photo-${photo.photoId}`}
          style={[s.card, { width, height }]}
        >
          <PlayerPhoto playerId={playerId} photoUrl={photo.photoUrl} box={{ kind: 'media' }} />
        </View>
      ))}
    </ScrollView>
  );
}

/**
 * **Height over width — the photo panel's 4:5**, read off its one owner, so a photo crops alike on
 * the panel and in the carousel, and the day the panel's shape moves this moves with it.
 */
const PHOTO_SHAPE = PHOTO_PANEL.record.height / PHOTO_PANEL.record.width;

/** Part 8's Strip gap. */
const STRIP_GAP = theme.space.sm;

const s = StyleSheet.create({
  // Part 8: the negative margin lets the strip bleed to the sheet's edge while its first card still
  // aligns to the gutter — as the Home rail's does.
  strip: { marginHorizontal: -theme.size.gutter },
  stripContent: { paddingHorizontal: theme.size.gutter, gap: STRIP_GAP },
  // The card's corner, clipping the media box inside it, which takes no corner of its own.
  card: { borderRadius: theme.radius.card, overflow: 'hidden' },
});
