/**
 * The concerns — the engine's own judgement about a term, in the engine's own voice.
 *
 * `concerns[]` is keyed by the same eight terms, ranked by points forgone, and **emitted by
 * the engine**. It gets its own table rather than the reason line in amber: a concern is the
 * *opposite claim about the same term*, so one sentence cannot serve both — and
 * [#233](https://github.com/Raketa02/Raketa/issues/233) §7 marks concerns **in place** on the
 * sheet, which makes reason and concern co-resident on one row rather than alternatives
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §7).
 *
 * **This is the one place in the deck that grades.** §4 forbids a reason line from doing it
 * precisely because this exists: the client never decides that a gap is wide, it renders the
 * sentence for a judgement that arrived ranked.
 *
 * ## Why it dispatches on evidence rather than on the term
 *
 * Three of the eight quote their own evidence — the intent mismatch is two sentences because
 * both directions fire and priced differently, and the two tag terms name the pair that
 * clashed. Keying on `term` would make those three take a second argument that could
 * disagree with the first; dispatching on the variant makes that unrepresentable, and it is
 * the same shape `reasonPresentation` takes for the same reason. The caller joins
 * `ConcernSchema.term` to the row it already holds.
 */

import { socialTagName } from '@/shared/vocabulary/socialTagPresentation';

import type { Evidence, TagPair } from '../domain/evidence';
import type { SearchMode } from '../domain/vocabulary';

/**
 * `INTENT_ALIGNMENT` is the one term whose concern is genuinely two sentences.
 *
 * [#230](https://github.com/Raketa02/Raketa/issues/230) priced both directions and **both
 * fire** — a for-fun candidate to a competitive searcher forgoes 16,1 points, the reverse
 * 10,0 — so a single wording would state one player's mismatch as the other's. The mode comes
 * off the evidence, never off the envelope: on the deck the envelope has none (§2).
 */
const INTENT_CONCERN: Readonly<Record<SearchMode, string>> = {
  COMPETITIVE: "They're here for a fun game, and you're not",
  FOR_FUN: "They're here to compete, and you're not",
};

/**
 * The sentence for a term the engine is concerned about, or nothing when it cannot be
 * written.
 *
 * The two tag terms are the only ones that can fail: their sentence **is** the pair that
 * clashed, and a term can be a concern with nothing clashing at all — its measured zero. The
 * line is dropped there rather than generalised, because *"you clash around the game"* with
 * no pair behind it is the client making the graded claim §7 reserves for the engine. The
 * card draws the next concern down; the sheet still marks the term in place.
 */
export function concernLine(evidence: Evidence): string | undefined {
  switch (evidence.kind) {
    case 'level_fit':
      return 'A wide level gap — the game may be one-sided';
    case 'predicted_balance':
      return 'Forecast to be uneven';
    case 'intent_alignment':
      return INTENT_CONCERN[evidence.myMode];
    case 'reliability':
      return 'Their record is thin on turning up';
    case 'availability_overlap':
      return 'Almost none of your week is theirs';
    case 'playing_style':
      return clashLine(evidence.clashing, 'on court');
    case 'social_vibe':
      return clashLine(evidence.clashing, 'around the game');
    case 'distance':
      return 'A long way out';
  }
}

/**
 * `{a} against {b} on court` — the pair, and where the two of them meet.
 *
 * **A gap is booked against these two sentences and not closed here.** §20.12 records it:
 * they read as neutral description, so a listener cannot hear the amber that a sighted reader
 * gets from the row's colour, and the clash word belongs beside these sentences rather than
 * inside an accessible name. Naming it here would be inventing the word §20.12 declined to
 * invent.
 */
function clashLine(clashing: readonly TagPair[], where: string): string | undefined {
  const [pair] = clashing;
  if (pair === undefined) return undefined;
  return `${socialTagName(pair.a)} against ${socialTagName(pair.b)} ${where}`;
}
