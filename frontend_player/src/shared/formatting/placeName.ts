/**
 * **The place, without the court** — the shorter value #335 chose over a second line.
 *
 * `Zabłocie Sport, court 3` is long because the value is long, and a venue's name is the half that
 * identifies it. The cut is at the **first comma, whatever follows it** — this reads no meaning
 * out of the value and never claims the tail was a court. That is affordable because nothing is
 * lost by it: the whole value is spoken in the surface's accessible name, and it is on the screen
 * either way. A place with no comma in it is already the shorter value and is drawn whole.
 *
 * **Never applied to a handle** — [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md)
 * §15 refuses that outright, which is why this takes a place and not a string.
 *
 * ## It left `features/conversations/` when the plan card arrived
 *
 * #335 states one rule for both Chats row kinds *"instead of two"*, and the plan's own `Where`
 * chip is the third surface it governs: a pinned card whose height depends on how much somebody
 * typed is chrome that moves the stream underneath it. Two implementations of *the shorter value*
 * would be two answers to one written rule, which is the drift `handleList.ts` was promoted beside
 * `playerName()` to prevent when the second row kind arrived
 * ([#366](https://github.com/Raketa02/Raketa/issues/366)).
 *
 * **What it is not is a cap.** A place with no comma in it and a hundred characters of venue is
 * still a hundred characters, and how many of them a chip or a row may draw is a measurement no
 * device has made — the surfaces that draw one say so where they draw it.
 */

export function placeWithoutTheCourt(place: string): string {
  const [named] = place.split(',');

  return named === undefined || named.trim() === '' ? place : named.trim();
}
