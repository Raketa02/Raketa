/**
 * Gender and Gender preference: **two vocabularies, and never one.**
 *
 * Both are settled by
 * [ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md).
 * They are separate types because they are separate facts, and their value sets do not even
 * have the same size — one enum doing both jobs would make *I am a woman* and *only women*
 * the same word.
 *
 * ## What the answers are, and what they are not
 *
 * The gender answer is **a statement about which searches a player wishes to appear in**,
 * not a ruling by the platform on who anybody is. A player whose identity is not on the list
 * picks the answer that puts them where they want to be seen, or takes *prefer not to say*
 * and appears in unconstrained searches only. Nothing here adjudicates anything.
 *
 * `prefer-not-to-say` is **an answer**, not a blank. The draft's `undefined` is *not asked
 * yet* and is a different thing entirely — the same distinction `proposalsOptIn` draws, and
 * for the same reason: the two are never quietly folded together.
 *
 * ## The preference is mutual, and that is the whole reason it is durable
 *
 * A preference governs **both directions**. It decides who a player sees *and* who may see
 * them, which is the difference between this and the browse filters it was written in
 * reaction to: a one-directional filter protects a woman's search and leaves her inbox open
 * to every man who searched for anybody. That is why it is a value held on the profile
 * rather than a switch on one search, and why `reachOf` exists — narrowing has a cost the
 * player must be told about **at the moment of setting**, not learn from silence.
 *
 * ## Nothing here is a gate
 *
 * The matching rule — a candidate is eligible only if they pass the searcher's preference
 * *and* the searcher passes theirs — is the backend's, and it is deliberately not
 * reimplemented here. What this file owns is the vocabulary the step offers and the one
 * consequence the step has to be able to say out loud.
 */

/** The three answers, as this app spells them. See `playerProfileMappers` for the wire's. */
export type Gender = 'woman' | 'man' | 'prefer-not-to-say';

/**
 * The order the step offers them in.
 *
 * The two named answers come in the record's own order, and **`prefer-not-to-say` is last
 * because it is not one of them**: it is the answer that declines the question, and an
 * answer that declines a question belongs after the question's answers rather than among
 * them. Nothing about the order is a recommendation — unlike the opt-in's, where *No*
 * leading is load-bearing, there is no answer here the product could be seen to prefer.
 */
export const GENDERS: readonly Gender[] = ['woman', 'man', 'prefer-not-to-say'];

/** Who a player is willing to be matched with. */
export type GenderPreference = 'women-only' | 'men-only' | 'any';

/**
 * The order the step offers them in — **widest first**.
 *
 * `any` leads because it is what the player already holds: the preference has a default and
 * a step that listed the two constraints first would read as asking a player to pick one.
 */
export const GENDER_PREFERENCES: readonly GenderPreference[] = ['any', 'women-only', 'men-only'];

/**
 * What a player holds who has never narrowed anything.
 *
 * **A real answer rather than an absence**, which is the difference between this field and
 * every `| undefined` in the draft: *no constraint* is exactly what `any` means, so there is
 * no third state for the step to collect and nothing for the commit to be short of. The
 * gender answer beside it is the opposite and is required — see `profileCommit`.
 */
export const DEFAULT_GENDER_PREFERENCE: GenderPreference = 'any';

/**
 * Who a narrowed preference makes a player invisible to.
 *
 * **This is the sentence the record requires and the reason it is a rule rather than copy.**
 * Setting *women only* does not merely filter what a player sees; because the gate is
 * mutual, it also hides them from every man — including men who searched for anybody. A
 * player who learned that from an empty inbox would have been told nothing at the moment it
 * mattered.
 *
 * A **reason code** and not a sentence, because the backend emits codes and the client
 * renders words
 * ([ADR-0022](../../../../../docs/adr/0022-kernel-negative-space-and-constant-homes.md)) —
 * and because the words are `genderPresentation`'s, testable apart from the rule that
 * decides whether they are shown at all.
 */
export type PreferenceReach =
  /** Nothing is narrowed, so nobody stops seeing this player. */
  | { readonly kind: 'unconstrained' }
  /** Narrowed. `hidden` is the side that can no longer reach this player at all. */
  | { readonly kind: 'narrowed'; readonly hidden: Exclude<Gender, 'prefer-not-to-say'> };

const REACH: Readonly<Record<GenderPreference, PreferenceReach>> = {
  any: { kind: 'unconstrained' },
  // Narrow to women and it is men who lose you, not women.
  'women-only': { kind: 'narrowed', hidden: 'man' },
  'men-only': { kind: 'narrowed', hidden: 'woman' },
};

export function reachOf(preference: GenderPreference): PreferenceReach {
  return REACH[preference];
}

/**
 * Whether this gender answer costs the player reach of its own.
 *
 * `prefer-not-to-say` matches an unconstrained search and never a narrowed one, so it is
 * the one answer that is **not free**. The record says plainly that the honest framing of
 * that cost is an unsolved copy problem; what is not in doubt is that the player has to know
 * about it before choosing, which is what this predicate is for.
 *
 * It is a separate question from `reachOf` — one is about the answer a player gives about
 * themselves, the other about the constraint they place on others — and folding them into
 * one *are you limiting yourself* would blur a distinction the whole feature rests on.
 */
export function costsReach(gender: Gender): boolean {
  return gender === 'prefer-not-to-say';
}
