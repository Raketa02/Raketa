/**
 * What a change costs, in the words a player reads before they make it.
 *
 * **The number is named.** "Some of your later answers" is the same sentence for one
 * answer and for six, and the difference between those two is the whole decision the
 * player is being asked to take. A consequence stated vaguely is a consequence performed
 * silently with a warning attached.
 *
 * **Zero later answers is its own sentence, not a count of nothing.** Changing the most
 * recent answer discards no others, so saying "0 later answers" would invent a cost;
 * saying nothing would imply the run carries on untouched, when what comes next is chosen
 * from the transcript this change produces. Both facts are short enough to state.
 *
 * Copy, so it lives beside the screen rather than in `domain/` — the count itself is the
 * domain's, in `proposeRevision`.
 */

export function revisionConsequence(discards: number): string {
  if (discards === 0) {
    return "This is the most recent answer you gave, so changing it discards no others — but what you're asked next may change.";
  }

  const answers = discards === 1 ? '1 later answer' : `${discards} later answers`;
  return `Changing it discards ${answers}. Each was asked because of what you said here, so you'll answer from this question on.`;
}
