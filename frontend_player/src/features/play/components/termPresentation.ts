/**
 * What each of the eight terms of Fit is **called** — the why-fit sheet's row heads.
 *
 * A `Readonly<Record<Term, string>>`, which is the first of the deck's two shapes: a code
 * with no payload gets a table keyed by the vocabulary, so a term added without words does
 * not compile ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1, §6.1).
 * The second shape — one function per variant — is `reasonPresentation`'s, because a reason
 * line is a sentence *over* a term's evidence and a flat table cannot hold one.
 *
 * **Eight, and `FAMILIARITY` is not among them.** It is a modifier, and the prototype's
 * *"Fresh faces"* naming it as a term is the defect this table corrects.
 *
 * The heads are plain nouns because the row states the figure beside them: *Level fit*, not
 * *How well your levels fit*, which would be the row grading itself before the number
 * arrives.
 */

import type { Term } from '../domain/vocabulary';

const LABEL: Readonly<Record<Term, string>> = {
  LEVEL_FIT: 'Level fit',
  PREDICTED_BALANCE: 'Predicted balance',
  INTENT_ALIGNMENT: 'The kind of evening',
  RELIABILITY: 'Their record',
  AVAILABILITY_OVERLAP: 'When you both play',
  PLAYING_STYLE: 'On court',
  SOCIAL_VIBE: 'Around the game',
  DISTANCE: 'How far',
};

export function termLabel(term: Term): string {
  return LABEL[term];
}
