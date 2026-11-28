/**
 * The yes stamp's longest words against the narrowest phone's card — measured rather than looked
 * at, because no device has drawn *I'M IN · 32,50 zł*
 * ([#719](https://github.com/Rakieta02/Rakieta/issues/719)).
 *
 * Until Q124 only a yes that charged at once carried the share; now every yes stamp does — a vote's
 * *I'M IN · 32 zł* and a payment's *PAY · 32 zł* — so the longest is a vote's with a share in
 * grosze, *I'M IN · 32,50 zł*, the ticket's own case. Two things could go wrong with it, and both
 * are checked:
 *
 * - **It wraps.** The stamp is a box drawn `inset` in from the card's edge with no far edge of its
 *   own, so a line longer than the room left goes onto a second line rather than running off.
 * - **Its corners leave the card.** It is tilted 12° about its centre, so its corners reach further
 *   than its box — sideways, and up towards the card's top edge.
 *
 * The widths are read off the Archivo ExtraBold and the IBM Plex Mono SemiBold in the bundle, as
 * `tabBadgeFit.test.ts` reads its figures: the words in the stamp's role, uppercased as the style
 * draws them, and the figure after them in mono, as it is written. On the day it was written the
 * line was **205,5pt**, its box 235,5 × 44 against 272pt of room, and tilted it reached from 16pt to
 * 255,5pt across the 290pt card and from 66pt below its top — room for a share of three figures,
 * *I'M IN · 123,50 zł*, too.
 *
 * **What makes it go red:** longer words on a stamp, a larger type role, more padding or stroke, a
 * wider inset or tilt, a wider page gutter, or a font release that redraws the letters. **What it
 * cannot see**: the card's width is the deck page's layout restated — the gutter either side, as
 * `GamesDeck`'s page pads it — so a margin added round the card must be added to `CARD` too.
 */

import { theme } from '@/shared/ui';
import { NARROWEST_SCREEN, readFace, widthOf } from '@/test-support/fontMetrics';

import type { DeckCard } from '../domain/deck';

import { STAMP } from './DeckStage';
import { STAMP_JOIN, stampsFor } from './deckPresentation';

/** The deck's page keeps the gutter on both sides, and the card takes the stage's width whole. */
const CARD = NARROWEST_SCREEN - 2 * theme.size.gutter;

const WORDS = theme.type.deckStamp;
const FIGURE = theme.num.xl;

const archivo = readFace(`@expo-google-fonts/archivo/${WORDS.fontFamily}.ttf`);
const plexMono = readFace(`@expo-google-fonts/ibm-plex-mono/${FIGURE.fontFamily}.ttf`);

/** The longest yes: a vote's, with a share in grosze. */
const LONGEST = stampsFor({ shareGrosze: 3250 } as DeckCard, false);

/** A stamp's one line, as the style draws it — the words shouted, the figure as it is written. */
function lineWidth(stamp: { readonly words: string; readonly figure?: string }): number {
  const words = widthOf(archivo, stamp.words.toUpperCase(), WORDS.fontSize, WORDS.letterSpacing);
  if (stamp.figure === undefined) return words;
  return (
    words + widthOf(plexMono, STAMP_JOIN + stamp.figure, FIGURE.fontSize, FIGURE.letterSpacing)
  );
}

/** The outlined box around one line. */
function box(stamp: { readonly words: string; readonly figure?: string }) {
  return {
    width: lineWidth(stamp) + 2 * (STAMP.padX + STAMP.stroke),
    height: Math.max(WORDS.lineHeight, FIGURE.lineHeight) + 2 * (STAMP.padY + STAMP.stroke),
  };
}

/** How far the box reaches from its centre once tilted — the transform turns it about its centre. */
function tiltedReach({ width, height }: { readonly width: number; readonly height: number }) {
  const angle = (STAMP.tilt * Math.PI) / 180;
  return {
    x: (width * Math.cos(angle) + height * Math.sin(angle)) / 2,
    y: (width * Math.sin(angle) + height * Math.cos(angle)) / 2,
  };
}

describe('the longest yes stamp, I’M IN · 32,50 zł, on the narrowest phone', () => {
  it('is the vote’s words with the share in grosze', () => {
    expect(LONGEST.yes).toEqual({ words: 'I’m in', figure: '32,50 zł' });
    const pay = stampsFor({ shareGrosze: 3250 } as DeckCard, true).yes;
    expect(lineWidth(pay)).toBeLessThan(lineWidth(LONGEST.yes));
  });

  it('stays on one line in the room the inset leaves it', () => {
    expect(box(LONGEST.yes).width).toBeLessThanOrEqual(CARD - STAMP.inset);
  });

  it('keeps its tilted corners inside the card — across, and below the top edge', () => {
    const drawn = box(LONGEST.yes);
    const reach = tiltedReach(drawn);
    const centre = { x: STAMP.inset + drawn.width / 2, y: STAMP.top + drawn.height / 2 };

    expect(centre.x - reach.x).toBeGreaterThanOrEqual(0);
    expect(centre.x + reach.x).toBeLessThanOrEqual(CARD);
    expect(centre.y - reach.y).toBeGreaterThanOrEqual(0);
  });

  it('leaves NOT THIS TIME inside the card as well, from the other edge', () => {
    const drawn = box(LONGEST.no);
    const reach = tiltedReach(drawn);
    const centre = CARD - STAMP.inset - drawn.width / 2;

    expect(drawn.width).toBeLessThanOrEqual(CARD - STAMP.inset);
    expect(centre - reach.x).toBeGreaterThanOrEqual(0);
    expect(centre + reach.x).toBeLessThanOrEqual(CARD);
  });
});
