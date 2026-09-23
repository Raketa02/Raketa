/**
 * **The court the reader shares with one person**, or nothing — the pair rule read for a single
 * name, for the radar's record sheet ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §5).
 *
 * The sheet reached from a radar card offers *Not today* and *Let's play* — unless a relation
 * already stands, and *a live challenge or game together, or one behind them* is one of those:
 * the foot names the court instead, and draws no buttons. This is the question the sheet asks,
 * answered off the list the tab bar already holds.
 *
 * ## Live first, and both must still be on it
 *
 * A court that stands holds the pair while **both** are still in it (`playersStillIn`) — a seat
 * given up releases that one person, and the reader who left is a stranger to the court again
 * whoever is still on it. `ON` counts as live for the whole life of the game and after it,
 * because the challenge never ends by being played (ADR-0172 §1): Karol's Saturday game is the
 * court the ticket names, days later.
 *
 * ## *One behind them* is one the Chats list still names
 *
 * The deck's cool-off holds a pair out of the deck for thirty days after a court is behind them,
 * and that number is ruleset configuration that **never crosses the wire**. So an ended court is
 * read here by the one notion of *recently behind* this client already has: it names the court
 * for exactly as long as the court's row is news on the Chats list (`belongsOnTheInbox`), and
 * not a moment longer — a lapsed challenge from a year ago is not a reason to refuse two people
 * a game, and a no of the reader's own leaves the list at once and names nothing here either.
 * A court the app cannot describe (a standing it has no words for) is not one it may name.
 *
 * Newest first within each, which is the list's own order and is not re-sorted here.
 */

import { challengeStands, playersStillIn, type Challenge } from './challenge';
import { belongsOnTheInbox } from './challengeInbox';

export function courtWith(
  challenges: readonly Challenge[],
  playerId: string,
  them: string,
): Challenge | undefined {
  const live = challenges.find((challenge) => {
    const stillIn = playersStillIn(challenge);
    return stillIn.includes(playerId) && stillIn.includes(them);
  });
  if (live !== undefined) return live;

  return challenges.find(
    (challenge) =>
      challenge.standing !== undefined &&
      !challengeStands(challenge) &&
      holdsASeat(challenge, playerId) &&
      holdsASeat(challenge, them) &&
      belongsOnTheInbox(challenge, playerId),
  );
}

function holdsASeat(challenge: Challenge, playerId: string): boolean {
  return challenge.seats.some((seat) => seat.playerId === playerId);
}
