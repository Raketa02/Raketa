/**
 * The tag's seventh variant, and the arithmetic that both licenses it and refuses the border
 * somebody will reach for next.
 *
 * [6.4](../../../docs/design-system.md#64-tag--the-status-pill) gained `volt` for Play's *they
 * want you* signal ([#309](https://github.com/Raketa02/Raketa/issues/309)), and it is the one
 * variant whose background is a **base** colour rather than a soft. The pair it rests on is
 * already in [2.5](../../../docs/design-system.md#25-contrast--computed) — so what this file
 * does is what `Switch.test.tsx`, `textOnMedia.test.ts` and `posterHues.test.ts` do for their
 * own published figures: **derive them, rather than let two documents drift.**
 *
 * The second block is the more useful one. Two figures are quoted as the **reason a volt border
 * is not drawn** — in `CandidateCard`'s module note and in Part 16's amendment row — and a
 * published number nothing computes is exactly what these tests exist to prevent. #309's
 * designs ask for a green border on the lifted card; 2.2's *a fill anywhere and a stroke only
 * on dark* refuses it, and this is that sentence as arithmetic.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View, type TextStyle, type ViewStyle } from 'react-native';

import { contrast, parse } from '@/test-support/contrast';

import { Tag } from './Tag';
import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1: 4.5:1 for text below the large-text threshold, and AAA at 7:1. */
const AA = 4.5;
const AAA = 7;

/** WCAG 1.4.11: a graphical object needs 3:1 against what is adjacent to it. */
const GRAPHICAL = 3;

describe('the volt tag', () => {
  it('is a volt fill under an ink label, and never the other way round', () => {
    render(<Tag label="Wants to play you" variant="volt" />);

    const pill = StyleSheet.flatten(screen.UNSAFE_getByType(View).props.style as ViewStyle);
    const label = StyleSheet.flatten(screen.UNSAFE_getByType(Text).props.style as TextStyle);

    expect(pill.backgroundColor).toBe(theme.color.volt);
    expect(label.color).toBe(theme.color.ink);
  });

  it('carries ink at the ratio 2.5 publishes, which is what a soft would have been for', () => {
    expect(ratio(theme.color.ink, theme.color.volt)).toBe(13.96);
    expect(ratio(theme.color.ink, theme.color.volt)).toBeGreaterThanOrEqual(AAA);
  });

  it('would carry white at 1,25 — Rule C read on the one colour it runs backwards on', () => {
    // Every other variant's label is the darker half of its pair. Volt inverts that: it is the
    // brightest value in the palette, so `ink` is the legible label and white is the refused
    // one. Pinned, because a reader who knows Rule C as *never white on coral or mint* will
    // eventually try white here.
    expect(ratio(theme.color.surface, theme.color.volt)).toBe(1.25);
    expect(ratio(theme.color.surface, theme.color.volt)).toBeLessThan(AA);
  });
});

/**
 * Why the signal is a **tag** and not a border.
 *
 * #309's designs draw the lifted card with a matching green outline. A border is a graphical
 * object, so 1.4.11 asks it for 3:1 against both sides — and volt clears neither. The
 * 2026-08-31 amendment refused *"a 2pt border on the interest card"* by name on this arithmetic
 * and concluded *"a border carries no word and this signal has one."*
 */
describe('volt as a stroke on paper', () => {
  it('is a line nobody sees, on a card and on the ground behind it', () => {
    expect(ratio(theme.color.volt, theme.color.surface)).toBe(1.25);
    expect(ratio(theme.color.volt, theme.color.paper)).toBe(1.12);
  });

  it('fails 1.4.11 at both, which is the whole of the refusal', () => {
    expect(ratio(theme.color.volt, theme.color.surface)).toBeLessThan(GRAPHICAL);
    expect(ratio(theme.color.volt, theme.color.paper)).toBeLessThan(GRAPHICAL);
  });

  it('clears it on dark, which is the half of 2.2 that is not a refusal', () => {
    expect(ratio(theme.color.volt, theme.color.night)).toBeGreaterThanOrEqual(GRAPHICAL);
  });
});
