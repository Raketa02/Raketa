/**
 * **The dealt deck's arithmetic** — where sign-in's three miniature cards stand once dealt, the box
 * the fan takes, and the scale that fits that box into the hero's room
 * ([#786](https://github.com/Raketa02/Raketa/issues/786), PRD #783; design system 12.2). No React
 * in any of it, for `deckStageGeometry`'s reason: a fan that crops on a small phone is a rule about
 * numbers, testable as numbers.
 *
 * ## The fan
 *
 * `size.stage.fan`, in the card's **drawing** points (`size.stage.card`, twice the mock's
 * miniature), so the fan and the card scale together: the two back cards' centres either side of
 * the front card's and a little below it, each turned outwards — the left one anticlockwise, the way
 * mock 2's *Picked for you* rises. The front card stays where the three were stacked, straight.
 *
 * ## The fit
 *
 * The hero's room is whatever the wordmark and the headline leave (`StageHero`), so it is measured
 * rather than computed: a short phone, a long headline at a large text size, a tall phone, each leave
 * a different one. The fan is scaled uniformly to the room's binding direction, and **never past
 * one** — the drawing size is the real card's own type, and a deck larger than that is a deck
 * nobody asked for. A room not yet measured has no size, and nothing is drawn in it.
 */

import { theme } from '@/shared/ui';

/** The three places on the stage, back to front: the two dealt cards, then the one that stays. */
export const DECK_PLACES = ['left', 'right', 'front'] as const;

export type DeckPlace = (typeof DECK_PLACES)[number];

/** Where a card stands, from the front card's own centre: points across, points down, degrees turned. */
export interface Placement {
  readonly x: number;
  readonly y: number;
  readonly turn: number;
}

/** A width and a height, in points. */
export interface Size {
  readonly width: number;
  readonly height: number;
}

/** The fan's box, and where in it the front card's centre is — from the box's top-left corner. */
export interface FanBox extends Size {
  readonly centre: { readonly x: number; readonly y: number };
}

const CARD = theme.size.stage.card;
const FAN = theme.size.stage.fan;

/** All three cards exactly on top of each other — before the deal, and the front card always. */
export const STACKED: Placement = { x: 0, y: 0, turn: 0 };

/** Where each card stands once the deck is dealt — see the module note. */
export const DEALT: Readonly<Record<DeckPlace, Placement>> = {
  left: { x: -FAN.across, y: FAN.down, turn: -FAN.turn },
  right: { x: FAN.across, y: FAN.down, turn: FAN.turn },
  front: STACKED,
};

/** The four corners of the card at `place`, dealt, around the front card's centre. */
function cornersOf(place: DeckPlace): readonly { readonly x: number; readonly y: number }[] {
  const { x, y, turn } = DEALT[place];
  const angle = (turn * Math.PI) / 180;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const halfW = CARD.width / 2;
  const halfH = CARD.height / 2;
  const corners: readonly (readonly [number, number])[] = [
    [-halfW, -halfH],
    [halfW, -halfH],
    [halfW, halfH],
    [-halfW, halfH],
  ];
  return corners.map(([cx, cy]) => ({ x: x + cx * cos - cy * sin, y: y + cx * sin + cy * cos }));
}

/** The smallest box holding the dealt fan, with the front card's centre placed in it. */
function boxOfTheFan(): FanBox {
  const corners = DECK_PLACES.flatMap(cornersOf);
  const xs = corners.map((corner) => corner.x);
  const ys = corners.map((corner) => corner.y);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  return {
    width: Math.max(...xs) - left,
    height: Math.max(...ys) - top,
    centre: { x: -left, y: -top },
  };
}

/** The dealt fan's box, at the drawing's size. */
export const FAN_BOX: FanBox = boxOfTheFan();

/** The scale that fits the dealt fan into `room` — the binding direction's, never past one. */
export function fitScale(room: Size): number {
  return Math.min(1, room.width / FAN_BOX.width, room.height / FAN_BOX.height);
}
