/**
 * **The other kind's door, and the panel it opens** — the words §28
 * ([ADR-0201](../../../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
 * §2, [#740](https://github.com/Raketa02/Raketa/issues/740)), for `KindDoor` beside it.
 *
 * Written once for each declared kind, so a competitive player's panel and a for-fun player's are
 * the same sentences read from the other side. Each cost line has a singular and a zero form, and
 * a zero drops the number (PRD #736, call 4) rather than saying *your 0 cards*.
 *
 * **The three answers are not here**: *Either suits me*, *Competitive* and *For fun* are
 * `playIntentPresentation`'s, the first-time question's and the You tab's words, and the panel
 * draws them from there.
 */

import { counted } from '@/shared/formatting/counted';

import type { DoorPanel } from '../domain/deck';
import type { GameKind } from '../domain/vocabulary';

import { PROPOSALS_COPY } from './proposalsCopy';

/** The kind before a noun — *competitive games*, *for-fun cards*. */
const BEFORE_A_NOUN: Readonly<Record<GameKind, string>> = {
  competitive: 'competitive',
  forFun: 'for-fun',
};

/** How the player plays — *You play padel competitively*, *You play padel for fun*. */
const HOW_YOU_PLAY: Readonly<Record<GameKind, string>> = {
  competitive: 'competitively',
  forFun: 'for fun',
};

/** The kind the player plays, and the kind they tapped. */
type DoorKinds = Pick<DoorPanel, 'yours' | 'tapped'>;

/** *You play padel competitively, so Raketa only puts you in competitive games.* */
export function doorTitle({ yours }: DoorKinds, sportInLine: string): string {
  return `You play ${sportInLine} ${HOW_YOU_PLAY[yours]}, so Raketa only puts you in ${BEFORE_A_NOUN[yours]} games.`;
}

/** *Want for-fun games too?* */
export function doorQuestion({ tapped }: DoorKinds): string {
  return `Want ${BEFORE_A_NOUN[tapped]} games too?`;
}

/** Under *Either suits me*: *Keep your 7 competitive cards and get for-fun ones too.* */
export function eitherCost({ yours, tapped, count }: DoorPanel): string {
  if (count === 0) {
    return `Get ${BEFORE_A_NOUN[tapped]} games as well as ${BEFORE_A_NOUN[yours]} ones.`;
  }
  const cards = counted(count, `${BEFORE_A_NOUN[yours]} card`, `${BEFORE_A_NOUN[yours]} cards`);
  return `Keep your ${cards} and get ${BEFORE_A_NOUN[tapped]} ones too.`;
}

/** Under the kind tapped: *Your 7 competitive cards go. Games you’re In on stay.* */
export function dropCost({ yours, count }: DoorPanel): string {
  const stay = 'Games you’re In on stay.';
  if (count === 0) return `Raketa stops dealing you ${BEFORE_A_NOUN[yours]} games. ${stay}`;
  const cards = counted(
    count,
    `${BEFORE_A_NOUN[yours]} card goes`,
    `${BEFORE_A_NOUN[yours]} cards go`,
  );
  return `Your ${cards}. ${stay}`;
}

/**
 * The way out, which sends nothing: *Keep competitive*, *Keep for fun* — the switch's own word for
 * the kind, inside a sentence.
 */
export function keepLabel({ yours }: DoorKinds): string {
  return `Keep ${PROPOSALS_COPY.kind[yours].toLowerCase()}`;
}

/**
 * **The door, spoken** — *For fun, not a kind you play*. Drawn, it is the kind's name alone and
 * dimmed; heard, the dimming has to be said, and a count it does not have is not said as *0 games*.
 */
export function doorSpoken(kind: GameKind): string {
  return `${PROPOSALS_COPY.kind[kind]}, not a kind you play`;
}
