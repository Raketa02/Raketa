/**
 * **The wire codes this feature keys copy by, spelled here** and held equal to the generated ones in
 * `mappers/wireVocabulary.ts` — so a code the backend adds fails `pnpm typecheck` in the one file
 * whose job is saying so, rather than reaching a screen with no words.
 */

/**
 * **Whether an invitation's link still works** — `valid`, or the three ways it no longer does: past
 * its 72 hours, already used to set a password, or locked by five wrong codes (ADR-0184 §4).
 */
export type InvitationLinkState = 'valid' | 'expired' | 'used' | 'locked';
