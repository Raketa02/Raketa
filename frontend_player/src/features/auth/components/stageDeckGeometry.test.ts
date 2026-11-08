/**
 * The dealt deck's arithmetic ([#786](https://github.com/Raketa02/Raketa/issues/786)) — where the
 * three cards stand once dealt, the box the fan takes, and the scale that fits it into the hero's
 * room. Held as numbers, because a fan that crops on a small phone is a rule about numbers, and a
 * device look on one phone proves it for that phone only.
 *
 * The corners are computed here independently of the module — a card's four corners, turned about
 * its centre and moved to its place — so the box is checked against the drawing rather than against
 * its own formula.
 */

import { theme } from '@/shared/ui';

import {
  DEALT,
  DECK_PLACES,
  FAN_BOX,
  STACKED,
  fitScale,
  type DeckPlace,
} from './stageDeckGeometry';

const CARD = theme.size.stage.card;

/** The four corners of the card at `place`, dealt, around the front card's centre. */
function cornersOf(place: DeckPlace): readonly { x: number; y: number }[] {
  const { x, y, turn } = DEALT[place];
  const angle = (turn * Math.PI) / 180;
  const halfW = CARD.width / 2;
  const halfH = CARD.height / 2;
  return [
    [-halfW, -halfH],
    [halfW, -halfH],
    [halfW, halfH],
    [-halfW, halfH],
  ].map(([cx = 0, cy = 0]) => ({
    x: x + cx * Math.cos(angle) - cy * Math.sin(angle),
    y: y + cx * Math.sin(angle) + cy * Math.cos(angle),
  }));
}

const EVERY_CORNER = DECK_PLACES.flatMap(cornersOf);

/** A hair's tolerance for floating point, far below a point. */
const HAIR = 1e-6;

describe('the fan', () => {
  it('leaves the front card where it was stacked, straight', () => {
    expect(DEALT.front).toEqual(STACKED);
    expect(STACKED).toEqual({ x: 0, y: 0, turn: 0 });
  });

  it('deals the two back cards as mirror images, out to either side, a little lower, turned outwards', () => {
    const { left, right } = DEALT;

    expect(left.x).toBeLessThan(0);
    expect(right.x).toBe(-left.x);
    expect(left.y).toBeGreaterThan(0);
    expect(right.y).toBe(left.y);
    // Turned outwards: the left card's top towards the left, the right card's towards the right —
    // a negative turn is anticlockwise on the screen, the way mock 2's *Picked for you* rises.
    expect(left.turn).toBeLessThan(0);
    expect(right.turn).toBe(-left.turn);
  });
});

describe('the fan’s box', () => {
  it('holds every corner of every dealt card, and is no larger than they are', () => {
    const box = FAN_BOX;
    const xs = EVERY_CORNER.map((corner) => corner.x + box.centre.x);
    const ys = EVERY_CORNER.map((corner) => corner.y + box.centre.y);

    expect(Math.min(...xs)).toBeCloseTo(0, 6);
    expect(Math.max(...xs)).toBeCloseTo(box.width, 6);
    expect(Math.min(...ys)).toBeCloseTo(0, 6);
    expect(Math.max(...ys)).toBeCloseTo(box.height, 6);
  });

  it('centres the front card across the box', () => {
    const box = FAN_BOX;

    expect(box.centre.x).toBeCloseTo(box.width / 2, 6);
  });
});

describe('the fit', () => {
  /**
   * Rooms the hero leaves the deck, from the roomiest to the meanest: a tall phone, a 390pt phone,
   * a 375 × 667 phone, and a 320pt phone with the headline at the text cap's three lines.
   */
  const ROOMS = [
    { width: 382, height: 220 },
    { width: 342, height: 184 },
    { width: 327, height: 140 },
    { width: 272, height: 60 },
  ];

  it.each(ROOMS)('fits the whole fan inside a $width × $height room', (room) => {
    const box = FAN_BOX;
    const scale = fitScale(room);

    expect(box.width * scale).toBeLessThanOrEqual(room.width + HAIR);
    expect(box.height * scale).toBeLessThanOrEqual(room.height + HAIR);
  });

  it('fills the room in the direction that binds', () => {
    const box = FAN_BOX;
    const room = { width: 342, height: 184 };
    const scale = fitScale(room);

    expect(
      Math.max((box.width * scale) / room.width, (box.height * scale) / room.height),
    ).toBeCloseTo(1, 6);
  });

  it('never draws the deck larger than it is drawn — the real card’s own type', () => {
    expect(fitScale({ width: 2000, height: 2000 })).toBe(1);
  });

  it('draws nothing in a room with no size yet', () => {
    expect(fitScale({ width: 0, height: 0 })).toBe(0);
  });
});
