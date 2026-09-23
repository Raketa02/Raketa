/**
 * *Remove this row.* **A noun and not a verb, like the card's dismissal**: what this creates is
 * the dismissal, recorded on the game the court became, for the reader alone
 * ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §5). There is no ask beyond the id, and nothing is folded here: what should be gone is the row
 * and the card, and the two lists' own reads are what say so.
 */

import { postDismissal } from '../api/challengesApi';

export async function dismissCourt(challengeId: string): Promise<void> {
  await postDismissal(challengeId);
}
