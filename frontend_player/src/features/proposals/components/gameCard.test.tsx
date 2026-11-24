/**
 * **The Games card sizes itself from what it measured** (#864) — the wiring between the card and
 * `deckCardGeometry`. Jest lays nothing out, so this suite plays the layout a phone would: the
 * card's own box, then each block's height, by `onLayout`. What it asserts is that the card draws
 * what the module says for those numbers, and when; the sizes themselves are
 * `deckCardGeometry.test.ts`'s, which holds them to the phones they were decided on.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet, type ViewStyle } from 'react-native';

import type { DeckCard, DeckPerson } from '../domain/deck';

import { cardGeometry, type CardBlocks, type CourtShape, type Size } from './deckCardGeometry';
import { GameCard } from './GameCard';

const HIDDEN_TOO = { includeHiddenElements: true } as const;
const READ_AT = Date.parse('2026-09-30T10:00:00Z');

/** The user's A32 once the row is gone — width-bound — and a 360 Android, height-bound. */
const A32: Size = { width: 354, height: 501.2 };
const SMALL: Size = { width: 330, height: 452.2 };

/** The decision log's §2 budget, as the A32 measured it. */
const MEASURED = { ribbon: 30, vs: 12, headline: 22, grid: 81, court: 71 } as const;

type Block = keyof typeof MEASURED | 'versions';

function person(name: string, extra: Partial<DeckPerson> = {}): DeckPerson {
  return { playerId: `id-${name}`, isYou: false, name, level: 2.7, isIn: false, ...extra };
}

const YOU = person('You', { isYou: true });

function card(extra: Partial<DeckCard> = {}): DeckCard {
  return {
    proposalId: 'p-1',
    type: 'PICKED_FOR_YOU',
    kind: 'competitive',
    startsAt: '2026-10-03T14:00:00Z',
    club: { id: 'club-1', name: 'Ogrody 33' },
    shareGrosze: 2700,
    deadline: '2026-10-02T14:00:00Z',
    inCount: 0,
    versionCount: 1,
    openSeatsAfterYourYes: 3,
    court: 'COURT_AVAILABLE',
    noFreeCancellation: false,
    sides: { yours: [YOU, person('Zofia')], theirs: [person('Ania'), person('Ewa')] },
    forecast: { pct: 87, provisional: false },
    overlap: { grade: 'GOOD', cells: [], game: { day: 6, range: 'AFTERNOON' } },
    ...extra,
  };
}

/**
 * The card on top, with its two doors, as the deck draws it. A card with none is a disabled press,
 * and Testing Library delivers no event — a layout included — inside a disabled responder.
 */
function cardOnTop(dealt: DeckCard, seatsPerSide = 2) {
  return (
    <GameCard
      card={dealt}
      seatsPerSide={seatsPerSide}
      at={READ_AT}
      day={undefined}
      today={1}
      onOpen={() => undefined}
      onPerson={() => undefined}
    />
  );
}

const drawCard = (dealt: DeckCard, seatsPerSide = 2) => render(cardOnTop(dealt, seatsPerSide));

const layout = (width: number, height: number) => ({
  nativeEvent: { layout: { x: 0, y: 0, width, height } },
});

/** Where each block's layout lands — the block, or the element it is measured round. */
const BLOCK: Readonly<Record<Block, () => Parameters<typeof fireEvent>[0]>> = {
  ribbon: () => screen.getByRole('header'),
  vs: () => screen.getByTestId('game-vs', HIDDEN_TOO),
  headline: () => screen.getByTestId('game-forecast'),
  grid: () => screen.getByTestId('overlap-grid'),
  court: () => screen.getByTestId('court-block-available'),
  versions: () => screen.getByText(/people are In/),
};

/** The phone lays the card out: its box — the stage's — and each block named, at its height. */
function layOut(stage: Size | undefined, blocks: Partial<Record<Block, number>>) {
  if (stage !== undefined) {
    fireEvent(screen.getByTestId('game-card-p-1'), 'layout', layout(stage.width, stage.height));
  }
  for (const [block, height] of Object.entries(blocks) as [Block, number][]) {
    fireEvent(BLOCK[block](), 'layout', layout(stage?.width ?? A32.width, height));
  }
}

const styleOf = (testId: string) =>
  StyleSheet.flatten(screen.getByTestId(testId, HIDDEN_TOO).props.style as ViewStyle);

/** Whether the card is drawn yet — it stands unseen until it has measured itself. */
const seen = () => styleOf('game-card-p-1').opacity !== 0;

/** A tile's drawn size, and how far it stands in from its column. */
function tile(name: string) {
  const { width, height, marginHorizontal } = styleOf(`game-tile-id-${name}`);
  return { width, height, inset: marginHorizontal };
}

/** What the module says for this room — the size the card should draw. */
function expected(stage: Size, shape: CourtShape, blocks: Omit<CardBlocks, 'hairline'>) {
  const { tiles } = cardGeometry({
    stage,
    shape,
    blocks: { ...blocks, hairline: StyleSheet.hairlineWidth },
  });
  return { width: tiles.width, height: tiles.height, inset: tiles.inset };
}

describe('the card measures itself before it is seen', () => {
  it('is drawn unseen until every block it draws has answered, then at the geometry’s size', () => {
    drawCard(card());
    expect(seen()).toBe(false);

    const { court: _late, ...early } = MEASURED;
    layOut(A32, early);
    expect(seen()).toBe(false);

    layOut(undefined, { court: MEASURED.court });
    expect(seen()).toBe(true);
    expect(tile('Zofia')).toEqual(expected(A32, 'doubles', MEASURED));
    expect(tile('Ania')).toEqual(expected(A32, 'doubles', MEASURED));
  });

  it('draws a singles card’s tiles at 3:4, with no vs line to wait for', () => {
    drawCard(card({ sides: { yours: [YOU], theirs: [person('Ania')] } }), 1);
    const { vs: _vs, ...singles } = MEASURED;
    layOut(A32, singles);

    expect(seen()).toBe(true);
    const drawn = tile('Ania');
    expect(drawn).toEqual(expected(A32, 'singles', singles));
    expect(Number(drawn.width) / Number(drawn.height)).toBeCloseTo(3 / 4, 6);
  });

  it('waits for the versions line where the card is dealt in versions', () => {
    drawCard(card({ versionCount: 2, inCount: 3 }));
    layOut(A32, MEASURED);
    expect(seen()).toBe(false);

    layOut(undefined, { versions: 12.5 });
    expect(seen()).toBe(true);
    expect(tile('Zofia')).toEqual(expected(A32, 'doubles', { ...MEASURED, versions: 12.5 }));
  });
});

describe('a card already measured', () => {
  it('keeps its size while a block that just appeared is measured, then makes room for it', () => {
    const { headline: _none, ...bare } = MEASURED;
    const { rerender } = drawCard(card({ forecast: undefined }));
    layOut(SMALL, bare);
    const before = expected(SMALL, 'doubles', bare);
    expect(tile('Zofia')).toEqual(before);

    rerender(cardOnTop(card()));
    // Never back to unseen, and never back to the size it stood at before it measured itself.
    expect(seen()).toBe(true);
    expect(tile('Zofia')).toEqual(before);

    layOut(undefined, { headline: MEASURED.headline });
    expect(tile('Zofia')).toEqual(expected(SMALL, 'doubles', MEASURED));
  });

  it('changes nothing for a block read again within a pixel, and resizes for a real change', () => {
    drawCard(card());
    layOut(SMALL, MEASURED);
    const before = tile('Zofia');

    // The gaps moved the court block onto another fraction of a pixel.
    layOut(undefined, { court: MEASURED.court + 0.2 });
    expect(tile('Zofia')).toEqual(before);

    // Its line wrapped: ten points less for each row of tiles to share.
    layOut(undefined, { court: MEASURED.court + 10 });
    expect(tile('Zofia')).toEqual(expected(SMALL, 'doubles', { ...MEASURED, court: 81 }));
    expect(tile('Zofia').height).toBeLessThan(Number(before.height));
  });
});
