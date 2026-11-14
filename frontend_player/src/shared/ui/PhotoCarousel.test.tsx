/**
 * **The photo carousel** — all of a player's photos, sideways, a card at a time
 * ([#799](https://github.com/Raketa02/Raketa/issues/799); the Home rows screens §6.3, §9.3; home rows
 * 23). The record draws it first; the vibe sheet (#803) draws the same one.
 *
 * Held here: the photos in their order, the card's share of the content width and its 4:5 shape, the
 * card's corner, the Strip's gap and bleed, the snap a card at a time, and nothing at all with no
 * photo. That it reads right on a phone is a look, owed.
 */

import { render, screen } from '@testing-library/react-native';
import { Dimensions, Image, ScrollView, StyleSheet, type ViewStyle } from 'react-native';

import { PhotoCarousel } from './PhotoCarousel';
import { PHOTO_PANEL } from './PlayerPhoto';
import { theme } from './theme';

const PHOTOS = [
  { photoId: 'photo-1', photoUrl: 'https://photos.test/1' },
  { photoId: 'photo-2', photoUrl: 'https://photos.test/2' },
  { photoId: 'photo-3', photoUrl: 'https://photos.test/3' },
];

/** Content width — the screen less the gutter each side (Part 4). */
const content = () => Dimensions.get('window').width - 2 * theme.size.gutter;
const cardWidth = () => content() * theme.size.photoCarouselRatio;

const strip = () => screen.UNSAFE_getByType(ScrollView);
const cards = () => screen.getAllByTestId(/^carousel-photo-/, { includeHiddenElements: true });
const styleOf = (node: { readonly props: { readonly style?: unknown } }) =>
  StyleSheet.flatten(node.props.style as ViewStyle) ?? {};

describe('the photo carousel', () => {
  it('draws every photo, in the order handed in', () => {
    render(<PhotoCarousel playerId="p-1" photos={PHOTOS} testID="record-photos" />);

    expect(
      screen
        .UNSAFE_getAllByType(Image)
        .map((image) => (image.props.source as { readonly uri: string }).uri),
    ).toEqual(['https://photos.test/1', 'https://photos.test/2', 'https://photos.test/3']);
    expect(screen.getByTestId('record-photos', { includeHiddenElements: true })).toBeTruthy();
  });

  it('draws each card at its share of the content width, 4:5, on the card’s corner', () => {
    render(<PhotoCarousel playerId="p-1" photos={PHOTOS} />);

    for (const card of cards()) {
      const style = styleOf(card);
      expect(style.width).toBeCloseTo(cardWidth());
      // The photo panel's own 4:5.
      expect(style.height).toBeCloseTo(cardWidth() * 1.25);
      expect(Number(style.height) / Number(style.width)).toBeCloseTo(
        PHOTO_PANEL.record.height / PHOTO_PANEL.record.width,
      );
      expect(style.borderRadius).toBe(theme.radius.card);
      expect(style.overflow).toBe('hidden');
    }
  });

  it('is Part 8’s Strip: the gap 9, bleeding past the gutter, snapping a card at a time', () => {
    render(<PhotoCarousel playerId="p-1" photos={PHOTOS} />);

    expect(styleOf(strip()).marginHorizontal).toBe(-theme.size.gutter);
    const inside = StyleSheet.flatten(strip().props.contentContainerStyle as ViewStyle);
    expect(inside.paddingHorizontal).toBe(theme.size.gutter);
    expect(inside.gap).toBe(theme.space.sm);
    expect(strip().props.horizontal).toBe(true);
    expect(strip().props.snapToInterval).toBeCloseTo(cardWidth() + theme.space.sm);
    expect(strip().props.decelerationRate).toBe('fast');
  });

  it('keeps a lone photo at the same size — a card, not the width', () => {
    render(<PhotoCarousel playerId="p-1" photos={PHOTOS.slice(0, 1)} />);

    expect(cards()).toHaveLength(1);
    expect(styleOf(cards()[0]!).width).toBeCloseTo(cardWidth());
  });

  it('draws nothing with no photo', () => {
    render(<PhotoCarousel playerId="p-1" photos={[]} testID="record-photos" />);

    expect(screen.queryByTestId('record-photos', { includeHiddenElements: true })).toBeNull();
    expect(screen.UNSAFE_queryAllByType(ScrollView)).toHaveLength(0);
  });
});
