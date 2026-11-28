/**
 * The tag's seventh variant, and the arithmetic under the border that arrives beside it.
 *
 * [6.4](../../../docs/design-system.md#64-tag--the-status-pill) gained `volt` for Play's *they
 * want you* signal ([#309](https://github.com/Rakieta02/Rakieta/issues/309)), and it is the one
 * variant whose background is a **base** colour rather than a soft. The pair it rests on is
 * already in [2.5](../../../docs/design-system.md#25-contrast--computed) — so what this file
 * does is what `Switch.test.tsx`, `textOnMedia.test.ts` and `posterHues.test.ts` do for their
 * own published figures: **derive them, rather than let two documents drift.**
 *
 * The second block is the more useful one, and it changed hands.
 * [#309](https://github.com/Rakieta02/Rakieta/issues/309) read *a fill anywhere and a stroke only
 * on dark* as refusing the green border its designs asked for, and shipped the two ratios as the
 * refusal. [#310](https://github.com/Rakieta02/Rakieta/issues/310) draws the border, so the block
 * now proves the narrower claim that survived: **volt itself still cannot be that stroke**, and
 * `voltStroke` — volt's meaning at a border's ratio, the relationship `coralInk` has to `coral` —
 * is what is drawn instead. Both halves are computed, because a published number nothing
 * computes is exactly what these tests exist to prevent.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View, type TextStyle, type ViewStyle } from 'react-native';

import {
  composite,
  contrast,
  hueAngle,
  hueDistance,
  parse,
  type Rgb,
} from '@/test-support/contrast';

import { TAG_HEIGHT, Tag } from './Tag';
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
 * Why the border on the lifted card is not drawn in `volt`.
 *
 * A border is a graphical object, so 1.4.11 asks it for 3:1 against both sides — and volt clears
 * neither. The 2026-08-31 amendment refused *"a 2pt border on the interest card"* by name on
 * this arithmetic, and that half of it stands: what #310 overruled is the sentence beside it,
 * which refused a **companion** dark enough to read.
 */
describe('volt as a stroke on paper', () => {
  it('is a line nobody sees, on a card and on the ground behind it', () => {
    expect(ratio(theme.color.volt, theme.color.surface)).toBe(1.25);
    expect(ratio(theme.color.volt, theme.color.paper)).toBe(1.12);
  });

  it('fails 1.4.11 at both, which is why the border is a second value and not this one', () => {
    expect(ratio(theme.color.volt, theme.color.surface)).toBeLessThan(GRAPHICAL);
    expect(ratio(theme.color.volt, theme.color.paper)).toBeLessThan(GRAPHICAL);
  });

  it('clears it on dark, which is the half of 2.2 that is not a refusal', () => {
    expect(ratio(theme.color.volt, theme.color.night)).toBeGreaterThanOrEqual(GRAPHICAL);
  });
});

/**
 * `voltStroke` — the stroke the marked card is actually drawn with, and the three figures 2.5
 * publishes for it.
 *
 * The third is the one an eye would have missed. A border that clears 1.4.11 against the card
 * and the ground behind it can still be invisible **as a change**, because what it replaces is
 * not the paper: it is `line`, the 1pt border every other card already has. So the ratio that
 * makes a marked card look marked is the one against `line`, and it is asserted here beside the
 * other two rather than left to the eye.
 */
describe('voltStroke as a stroke on paper', () => {
  it('clears 1.4.11 on the card and on the ground behind it', () => {
    expect(ratio(theme.color.voltStroke, theme.color.surface)).toBe(4.01);
    expect(ratio(theme.color.voltStroke, theme.color.paper)).toBe(3.58);

    expect(ratio(theme.color.voltStroke, theme.color.surface)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(ratio(theme.color.voltStroke, theme.color.paper)).toBeGreaterThanOrEqual(GRAPHICAL);
  });

  it('clears it against the border it replaces, which is what makes the mark legible', () => {
    expect(ratio(theme.color.voltStroke, theme.color.line)).toBe(3.07);
    expect(ratio(theme.color.voltStroke, theme.color.line)).toBeGreaterThanOrEqual(GRAPHICAL);
  });

  it('is volt’s own family and not amber’s, which is the only hue it could be read as', () => {
    // Colour is picked by meaning, and this one's meaning is volt's. 7 deg is *the same green*;
    // `amber` is the only other dark warm value in the palette, and 37 deg is not it.
    const hue = (value: string) => hueAngle(parse(value).rgb);

    expect(hueDistance(hue(theme.color.voltStroke), hue(theme.color.volt))).toBeLessThan(10);
    expect(hueDistance(hue(theme.color.voltStroke), hue(theme.color.amber))).toBeGreaterThan(25);
  });

  it('is never a text bed, which is what keeps the word on the volt fill beside it', () => {
    // Both below AA. The border carries no word by construction — Part 13's *never colour
    // alone* is satisfied by the tag, and this is the second copy of a cue that is already one.
    expect(ratio(theme.color.surface, theme.color.voltStroke)).toBeLessThan(AA);
    expect(ratio(theme.color.ink, theme.color.voltStroke)).toBeLessThan(AA);
  });
});

/**
 * `arranging` — the dot on the Now card's tag while the game is still in the players' hands
 * ([#413](https://github.com/Rakieta02/Rakieta/issues/413)), and the figures `theme.ts` publishes
 * for it.
 *
 * **The mock's dot was measured and found to be `amber`.** `#87641A` is a degree off amber's hue
 * and a step off its lightness, and it sits at 1,61 against the tag it is drawn in — the value the
 * ticket itself calls invisible on `night`. So the hue and the saturation are the mock's and only
 * the lightness is raised, to the step past the first that clears 1.4.11 on the tag's own ground.
 * Both halves are computed here: the value that was refused, and the one drawn instead.
 */
describe('the arranging dot on night', () => {
  /** What a dot inside an on-dark tag is actually adjacent to: the tag's white, over `night`. */
  const onNight = (translucent: string) => {
    const { rgb, alpha } = parse(translucent);
    return composite(rgb, alpha, parse(theme.color.night).rgb);
  };
  const tagGround = onNight(theme.color.onDarkTag);
  const fillGround = onNight(theme.color.onDarkFill);

  it('clears 1.4.11 on the night card, on the tag it sits in, and on the icon door beside it', () => {
    expect(ratio(theme.color.arranging, theme.color.night)).toBe(5.35);
    expect(contrast(parse(theme.color.arranging).rgb, tagGround)).toBe(3.49);
    expect(contrast(parse(theme.color.arranging).rgb, fillGround)).toBe(3.17);

    expect(contrast(parse(theme.color.arranging).rgb, tagGround)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(parse(theme.color.arranging).rgb, fillGround)).toBeGreaterThanOrEqual(
      GRAPHICAL,
    );
  });

  it('is the value the mock drew, lifted — and the mock’s own value would not have been seen', () => {
    // Measured off `planning/1_planning_game_card1.png` at 1×, as the pixels read: #87641A.
    const MOCK: Rgb = [135, 100, 26];
    const hue = (value: string) => hueAngle(parse(value).rgb);

    expect(contrast(MOCK, tagGround)).toBeLessThan(GRAPHICAL);
    expect(contrast(MOCK, parse(theme.color.night).rgb)).toBeLessThan(GRAPHICAL);
    // The same hue, so it is the mock's dot and not a colour chosen in its place.
    expect(hueDistance(hue(theme.color.arranging), hueAngle(MOCK))).toBeLessThan(2);
  });

  it('is nobody else’s family: not coral’s, not volt’s, and not a fifth sport’s', () => {
    const hue = (value: string) => hueAngle(parse(value).rgb);

    expect(hueDistance(hue(theme.color.arranging), hue(theme.color.coral))).toBeGreaterThan(25);
    expect(hueDistance(hue(theme.color.arranging), hue(theme.color.volt))).toBeGreaterThan(25);
    expect(hueDistance(hue(theme.color.arranging), hue(theme.color.mint))).toBeGreaterThan(25);
  });
});

describe('the more tag (#803)', () => {
  const boxOf = (variant: 'ok' | 'more') => {
    render(<Tag label="+2 more" variant={variant} />);
    const box = StyleSheet.flatten(
      screen.getByText('+2 more').parent?.parent?.props.style as ViewStyle,
    );
    screen.unmount();
    return box;
  };
  const edge = (box: ViewStyle, padding: 'paddingVertical' | 'paddingHorizontal') =>
    Number(box[padding] ?? 0) + Number(box.borderWidth ?? 0);

  it('is dashed in line, its words muted, on no bed of its own', () => {
    const more = boxOf('more');
    expect(more.borderStyle).toBe('dashed');
    expect(more.borderColor).toBe(theme.color.line);
    expect(more.backgroundColor).toBeUndefined();
    render(<Tag label="+2 more" variant="more" />);
    expect(StyleSheet.flatten(screen.getByText('+2 more').props.style as TextStyle).color).toBe(
      theme.color.muted,
    );
  });

  it('keeps every tag’s box: its border stands in the padding’s first point, so a line of chips stays one height', () => {
    const more = boxOf('more');
    const ok = boxOf('ok');
    expect(edge(more, 'paddingVertical')).toBe(edge(ok, 'paddingVertical'));
    expect(edge(more, 'paddingHorizontal')).toBe(edge(ok, 'paddingHorizontal'));
  });
});

describe('TAG_HEIGHT (#803)', () => {
  it('is the box every variant draws: the label’s line and the padding either side', () => {
    for (const variant of ['ok', 'more'] as const) {
      render(<Tag label="+2 more" variant={variant} />);
      const box = StyleSheet.flatten(
        screen.getByText('+2 more').parent?.parent?.props.style as ViewStyle,
      );
      const edge = Number(box.paddingVertical ?? 0) + Number(box.borderWidth ?? 0);
      expect(theme.type.tag.lineHeight + 2 * edge).toBe(TAG_HEIGHT);
      screen.unmount();
    }
  });
});
