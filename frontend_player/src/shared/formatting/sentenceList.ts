/**
 * **The platform's own join for a list inside a sentence** — commas, and a final *and*.
 *
 * [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §22.6 states it once, for the
 * game screen's checklist — *"joined with commas and a final and: `where and the hour`, `where,
 * the day and the hour`"* — and it is the same rule §24.2's spoken row already follows. The
 * conjunction is what says where a list stops: a listener hearing a flat comma run has no way to
 * tell the last item from the next fact in the sentence, and a reader has only the full stop.
 *
 * **Promoted on the third caller and not the second**, which is `docs/architecture.md`'s rule and
 * `recoveryMessage`'s precedent. Two spellings of it had grown up apart — `spokenHandles`, which
 * joins the people in a room, and `gamePresentation`'s court list, which joins the people you
 * played — and the checklist's three slot names is the one that made a fourth private copy the
 * obvious wrong answer. What each caller keeps is what is genuinely its own: `spokenHandles` keeps
 * *the spoken list never truncates*, and the court list keeps its lead.
 *
 * It is deliberately **not** `handleList`'s: that module is about handles and about what fits in a
 * `cardTitle`, and reaching into it to join three slot names would be borrowing a rule about
 * people to say something about a plan.
 */

/** What separates two items in a list of them. Structure rather than voice. */
export const LIST_SEPARATOR = ', ';

/** The word before the last item, so a listener hears where the list ends. */
export const FINAL_CONJUNCTION = ' and ';

/**
 * `where`, `where and the hour`, `where, the day and the hour` — **nothing is dropped.**
 *
 * An empty list is the empty string, which every caller here treats as *there is no list to say*
 * rather than as a value: the sentence around it is chosen before this is reached.
 */
export function sentenceList(parts: readonly string[]): string {
  if (parts.length <= 1) return parts.join('');

  const said = [...parts];
  const last = said.pop();

  return `${said.join(LIST_SEPARATOR)}${FINAL_CONJUNCTION}${last}`;
}
