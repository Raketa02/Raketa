/**
 * **Sign-up's podium, as numbers** — the three places, the order they stand and rise in, and the box
 * the podium takes, which is fitted into the hero's room
 * ([#788](https://github.com/Raketa02/Raketa/issues/788), PRD #783; design system 12.2). No React in
 * it, for `stageDeckGeometry`'s reason: a podium that crops on a small phone is a rule about numbers.
 *
 * ## A column, top to bottom
 *
 * A player's tile, `space.xxs`, their name on one line, `space.xs`, and their step — mock 5's gaps at
 * 2,1 pixels to the point, put on the 3pt grid. The three columns stand on one baseline, a step's
 * width each and `space.sm` apart, so the tallest — the first's, You on the volt step — sets the
 * box's height.
 *
 * **The name's line is counted at the text cap** (`textMaxScale`), the largest it can be drawn: the
 * box is what is fitted into the room, and a box measured at the system text size would let a large
 * text size push You's tile over the wordmark. At the system size the podium stands a little under
 * the box's top, which is room nobody sees, since it stands on the box's foot.
 *
 * ## The fit
 *
 * The box is scaled whole into the room, never up (`scaleInto`), centred across it and **standing on
 * its foot**, so on a tall room the steps keep to the headline and the night is over You. The plate
 * is scaled about its own centre, so its top is set where, once scaled, its foot lands on the room's.
 */

import { theme } from '@/shared/ui';

import { scaleInto, type Size } from './stageFit';

/** The three places on the podium. */
export const PODIUM_PLACES = ['first', 'second', 'third'] as const;

export type PodiumPlace = (typeof PODIUM_PLACES)[number];

/** Left to right, as they stand: 2, 1, 3. */
export const STANDING_ORDER = [
  'second',
  'first',
  'third',
] as const satisfies readonly PodiumPlace[];

/** The order the steps rise in, and their players land: the third, the second, the first. */
export const RISING_ORDER = ['third', 'second', 'first'] as const satisfies readonly PodiumPlace[];

const PODIUM = theme.size.stage.podium;

/** Between a player's tile and their name. */
export const FACE_TO_NAME = theme.space.xxs;

/** Between a player's name and their step. */
export const NAME_TO_STEP = theme.space.xs;

/** A name's line, at the largest the text cap lets it be drawn — see the module note. */
const NAME_LINE = theme.type.cardTitle.lineHeight * theme.size.stage.textMaxScale;

/** A column's height, the tile's top to the step's foot. */
const columnHeight = (place: PodiumPlace) =>
  PODIUM.face[place] + FACE_TO_NAME + NAME_LINE + NAME_TO_STEP + PODIUM.step[place];

/** The podium's box, at its drawing size. */
export const PODIUM_BOX: Size = {
  width: PODIUM_PLACES.length * PODIUM.stepWidth + (PODIUM_PLACES.length - 1) * theme.space.sm,
  height: Math.max(...PODIUM_PLACES.map(columnHeight)),
};

/** Where the podium's box is drawn in `room`: its scale, and its unscaled top-left corner. */
export interface PodiumPlate {
  readonly scale: number;
  readonly left: number;
  readonly top: number;
}

/** The box fitted into `room` — see the module note. */
export function podiumPlate(room: Size): PodiumPlate {
  const scale = scaleInto(room, PODIUM_BOX);
  return {
    scale,
    left: (room.width - PODIUM_BOX.width) / 2,
    top: room.height - (PODIUM_BOX.height * (1 + scale)) / 2,
  };
}
