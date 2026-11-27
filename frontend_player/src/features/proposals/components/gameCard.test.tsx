/**
 * **The Games card sizes itself from what it measured** (#864, #865) — the wiring between the card
 * and `deckCardGeometry`. Jest lays nothing out, so this suite plays the layout a phone would: the
 * card's own box, then each block's height, by `onLayout`. What it asserts is that the card draws
 * what the module says for those numbers, and when; the sizes themselves are
 * `deckCardGeometry.test.ts`'s, which holds them to the phones they were decided on.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet, type ViewStyle } from 'react-native';

import { theme } from '@/shared/ui/theme';

import type { DeckCard, DeckPerson } from '../domain/deck';

import { cardGeometry, type CardBlocks, type CourtShape, type Size } from './deckCardGeometry';
import { GameCard } from './GameCard';
import { PROPOSALS_COPY } from './proposalsCopy';

const HIDDEN_TOO = { includeHiddenElements: true } as const;
const READ_AT = Date.parse('2026-09-30T10:00:00Z');

/** The user's A32 once the row is gone — width-bound — and a 360 Android, height-bound. */
const A32: Size = { width: 354, height: 501.2 };
const SMALL: Size = { width: 330, height: 452.2 };

/**
 * The decision log's §2 budget, as the A32 measured it — the grid by its words, the grade over the
 * day letters: 42 of its 81, its cells being the geometry's (#865).
 */
const MEASURED = { ribbon: 30, vs: 12, headline: 22, gridWords: 42, court: 71 } as const;

/** The 320 × 568's stage — where the card does not fit, and the deck scrolls. */
const SE: Size = { width: 290, height: 276.4 };

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
function cardOnTop(
  dealt: DeckCard,
  seatsPerSide = 2,
  onLeast: (proposalId: string, least: number | undefined) => void = () => undefined,
) {
  return (
    <GameCard
      card={dealt}
      seatsPerSide={seatsPerSide}
      at={READ_AT}
      day={undefined}
      today={1}
      onOpen={() => undefined}
      onPerson={() => undefined}
      onLeast={onLeast}
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
  gridWords: () => screen.getByTestId('overlap-words'),
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

/** What the module says for this room. */
const geometryFor = (stage: Size, shape: CourtShape, blocks: Omit<CardBlocks, 'hairline'>) =>
  cardGeometry({ stage, shape, blocks: { ...blocks, hairline: StyleSheet.hairlineWidth } });

/** The size the card should draw its tiles. */
function expected(stage: Size, shape: CourtShape, blocks: Omit<CardBlocks, 'hairline'>) {
  const { tiles } = geometryFor(stage, shape, blocks);
  return { width: tiles.width, height: tiles.height, inset: tiles.inset };
}

/** A word's own cap, as the element drawing it carries it. */
const capOf = (words: string): unknown =>
  screen.getByText(words, HIDDEN_TOO).props.maxFontSizeMultiplier;

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

describe('a tile’s words are capped (#865)', () => {
  const CAP = theme.size.gameCard.footMaxScale;

  it('caps every word in a player’s foot: the name, IN, FRIEND and the level line', () => {
    drawCard(
      card({
        sides: {
          yours: [YOU, person('Zofia', { isIn: true, friend: true })],
          theirs: [person('Ania', { paid: true }), person('Ewa')],
        },
      }),
    );
    expect(CAP).toBe(1.3);
    expect(capOf('Zofia')).toBe(CAP);
    expect(capOf(PROPOSALS_COPY.in)).toBe(CAP);
    expect(capOf(PROPOSALS_COPY.friend)).toBe(CAP);
    expect(capOf('2,70 · paid')).toBe(CAP);
    // One line each: a level line that wrapped would be a foot taller than the one the cap is for.
    expect(screen.getByText('2,70 · paid').props.numberOfLines).toBe(1);
  });

  it('caps *You complete it* on your own tile', () => {
    drawCard(card({ openSeatsAfterYourYes: 0 }));
    expect(capOf(PROPOSALS_COPY.youCompleteIt)).toBe(CAP);
  });

  it('caps a rescue’s open seat: its words and its price', () => {
    drawCard(card({ type: 'SEAT_OPEN', openSeatsAfterYourYes: 0 }));
    expect(capOf(PROPOSALS_COPY.youCompleteIt)).toBe(CAP);
    expect(capOf('27 zł · court booked')).toBe(CAP);
  });

  it('leaves the rest of the card’s words to the OS text size', () => {
    drawCard(card());
    expect(capOf(PROPOSALS_COPY.grade.GOOD)).toBeUndefined();
  });
});

describe('short room (#865)', () => {
  /** A row of the grid's cells, as drawn — it carries the cells' height. */
  const cellHeight = () =>
    StyleSheet.flatten(
      screen.getByTestId('overlap-row-MORNING', HIDDEN_TOO).props.style as ViewStyle,
    ).height;
  const body = () =>
    StyleSheet.flatten(screen.getByTestId('game-card-body', HIDDEN_TOO).props.style as ViewStyle);

  it('draws the grid’s cells, the body’s padding above and below and its tiles at the geometry’s share', () => {
    drawCard(card());
    layOut(SMALL, MEASURED);
    const at = geometryFor(SMALL, 'doubles', MEASURED);
    expect(at.scale).toBeLessThan(1);

    expect(cellHeight()).toBeCloseTo(theme.size.gameCard.cell * at.scale, 6);
    expect(body()).toMatchObject({ paddingVertical: at.padY, paddingHorizontal: at.padX });
    expect(tile('Zofia')).toEqual(expected(SMALL, 'doubles', MEASURED));
  });

  it('draws the grid at rest where the card has room', () => {
    drawCard(card());
    layOut(A32, MEASURED);
    expect(cellHeight()).toBe(theme.size.gameCard.cell);
  });
});

describe('its least height (#865)', () => {
  it('tells the deck how short it can get, once it has measured itself', () => {
    const onLeast = jest.fn();
    render(cardOnTop(card(), 2, onLeast));
    expect(onLeast).not.toHaveBeenCalled();

    layOut(SE, MEASURED);
    const { least } = geometryFor(SE, 'doubles', MEASURED);
    expect(least).toBeGreaterThan(SE.height);
    expect(onLeast).toHaveBeenLastCalledWith('p-1', least);
  });

  it('tells it again when a block grows', () => {
    const onLeast = jest.fn();
    render(cardOnTop(card(), 2, onLeast));
    layOut(SE, MEASURED);
    layOut(undefined, { court: MEASURED.court + 10 });
    expect(onLeast).toHaveBeenLastCalledWith(
      'p-1',
      geometryFor(SE, 'doubles', { ...MEASURED, court: 81 }).least,
    );
  });
});

describe('a card its stage cannot hold yet (#865)', () => {
  it('stays unseen until the deck lays the stage out at its least, then is never unseen again', () => {
    drawCard(card());
    layOut(SE, MEASURED);
    // Measured, and at its floor in a stage too short for it: shown now, it would be cut off at the
    // foot until the stage grew.
    expect(seen()).toBe(false);

    const { least } = geometryFor(SE, 'doubles', MEASURED);
    layOut({ ...SE, height: least }, {});
    expect(seen()).toBe(true);

    // A block that grows later keeps it seen while the deck makes room.
    layOut(undefined, { court: MEASURED.court + 10 });
    expect(seen()).toBe(true);
  });

  it('is seen at once where nobody lays a stage out for it', () => {
    render(
      <GameCard
        card={card()}
        seatsPerSide={2}
        at={READ_AT}
        day={undefined}
        today={1}
        onOpen={() => undefined}
      />,
    );
    layOut(SE, MEASURED);
    expect(seen()).toBe(true);
  });

  it('takes its least back when it leaves', () => {
    const onLeast = jest.fn();
    const { unmount } = render(cardOnTop(card(), 2, onLeast));
    layOut(SE, MEASURED);
    unmount();
    expect(onLeast).toHaveBeenLastCalledWith('p-1', undefined);
  });
});
