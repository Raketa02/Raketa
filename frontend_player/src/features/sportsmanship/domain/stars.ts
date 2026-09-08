/**
 * **Stars, and the answer one card carries.** The word *rating* is Skill rating's on this
 * platform, so everything here is spelled *stars* or *the card*
 * ([`CONTEXT.md`](../../../../../CONTEXT.md) · Sportsmanship).
 *
 * ## The scale is one to five whole stars, and the missing sixth value is the point
 *
 * There is **no zero** — a rating that reads as *worthless* is a weapon out of proportion to a
 * tap, and one star already dents an average about as hard — and there are **no halves**,
 * because five taps is one number. `Stars` is the five, spelled, so a value off the scale is a
 * compile error at every site that constructs one and `stars_are_one_to_five` is a refusal
 * this client cannot earn.
 *
 * ## Blank is an absence and nothing else
 *
 * Not a zero, not a null and not a row: leaving somebody out of the answer is what leaves them
 * blank, and the draft spells that as a key that is not there. The consequence a `Record` gives
 * for free is the other half of it — **one card carries one answer about each player**, which
 * the backend refuses by name (`you_rated_the_same_person_twice`, *refused rather than
 * collapsed, because collapsing means the platform picking which of your two opinions to
 * keep*) and this shape cannot express.
 *
 * ## Pressing the star that already stands clears the row
 *
 * The one gesture that makes a mis-tap survivable, and it is **a rule about what an answer is**
 * rather than about a drawing — which is why it lives here and not in `StarRow`. Submitting
 * closes the card for ever and there is no correction path, so a row that could only ever go up
 * would take *leave anybody blank* away from the one person who needs it: somebody whose finger
 * slipped.
 *
 * ## The court is what the answer is read against
 *
 * {@link starsGiven} takes the players the card asks about and reads the draft through them, so
 * stars for somebody who was not on that court cannot be sent — `they_were_not_on_this_court` is
 * a 400 the backend spells *including yourself*, and the fence is the signature rather than a
 * check somebody remembers to run.
 */

/** One to five, whole. The scale, spelled — see the module note. */
export type Stars = 1 | 2 | 3 | 4 | 5;

/** Whether a number is on the scale at all. The one gate into {@link Stars}. */
export function isStars(value: number): value is Stars {
  return Number.isInteger(value) && value >= 1 && value <= 5;
}

/**
 * What the player has said so far — **a player id to their stars, and absence is blank.**
 *
 * Held for as long as the card is on screen and no longer. There is nothing to resume: a card
 * is answered once, in one sitting, and a draft that outlived the list it was typed on would be
 * an opinion about an evening the player is no longer looking at.
 */
export type StarsDraft = Readonly<Record<string, Stars>>;

/** Nobody rated, which is where every card starts and is a state it may also be sent in. */
export const NOTHING_SAID: StarsDraft = {};

/** What stands about one person, or nothing at all. */
export function starsFor(draft: StarsDraft, playerId: string): Stars | undefined {
  return draft[playerId];
}

/**
 * One press on one person's row — **the star pressed, or the row cleared when it already
 * stood.**
 *
 * A press off the scale is ignored rather than stored. It is unreachable from a row that draws
 * exactly five, and refused here anyway for the reason the module note gives: the scale is a
 * rule about answers, not about a drawing.
 */
export function pressed(draft: StarsDraft, playerId: string, value: number): StarsDraft {
  if (!isStars(value)) return draft;

  if (draft[playerId] === value) {
    const { [playerId]: _cleared, ...rest } = draft;
    return rest;
  }

  return { ...draft, [playerId]: value };
}

/** One person on the card, and the stars they were given. */
export interface StarsGiven {
  readonly playerId: string;
  readonly stars: Stars;
}

/**
 * The answer, **in the card's own order** — everybody the player rated, and nobody else.
 *
 * An empty list is an answer: it closes the card without rating anybody, which is an explicit
 * *I am not rating anyone* rather than a card left to expire.
 */
export function starsGiven(draft: StarsDraft, players: readonly string[]): readonly StarsGiven[] {
  return players.flatMap((playerId) => {
    const stars = draft[playerId];
    return stars === undefined ? [] : [{ playerId, stars }];
  });
}
