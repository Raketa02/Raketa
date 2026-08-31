/**
 * The **Play intent**: what kind of game a player wants in one sport.
 *
 * Three values, and `NO_PREFERENCE` is an **explicit answer** rather than a null — *either
 * suits me* and *I never opened that screen* are different facts, and the matcher has to be
 * able to tell them apart ([ADR-0094](../../../../docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)).
 * There is no unanswered value here to represent: absence lives in the map that carries the
 * declarations, not in the vocabulary.
 *
 * ## Why this is `shared/` and not `play/domain/`
 *
 * It began in `features/play/domain/vocabulary.ts`, because Play was the only feature that had
 * met one. `player_profile` is the second — it **serves** the declaration on the profile
 * surface and **writes** it on `PUT /play-intents/{sport}` — and a Play intent is a term in the
 * root glossary rather than either feature's reading of one, which is `shared/README.md`'s own
 * test: *"whether a second feature would have written the identical table."* It would have
 * written this one exactly, and a second list of three intents is the drift `sport.ts` and
 * `week.ts` were promoted to stop.
 *
 * **That test is not "two files use it."** What is proven here is *ownership*: the three are
 * ADR-0094's, fixed by a release rather than by either feature, and neither feature may change
 * them. What each feature *does* with one stayed behind — which `SearchMode` a declaration
 * seeds (`play/domain/playMode`), and which screen may write one
 * (`player_profile/use-cases/declarePlayIntent`) — and so did every word either feature says
 * about one.
 *
 * **The move also breaks a cycle, and that is a symptom rather than the reason.** Reached
 * through `features/play/types.ts`, this list made `player_profile`'s mapper import Play's
 * public surface while Play's public surface exports a screen built out of `player_profile`'s
 * — a module cycle whose failure mode is an empty membership set at load, silently dropping
 * every declaration. A vocabulary neither feature owns had no business travelling through
 * either one's front door.
 *
 * The wire spells these identically, so unlike a `Sport` there is no second spelling and no
 * mapper: the agreement with the contract is asserted by the compiler in
 * `features/play/mappers/wireVocabulary.ts`.
 */

/**
 * The three declarations, in the order a screen offers them.
 *
 * The type is derived from the list rather than declared beside it, so the two cannot
 * disagree — `SOCIAL_TAG_IDS`' shape, and for its reason: the array is the runtime membership
 * test a build eight months old needs when a fourth value arrives.
 */
export const PLAY_INTENTS = ['COMPETITIVE', 'FOR_FUN', 'NO_PREFERENCE'] as const;

export type PlayIntent = (typeof PLAY_INTENTS)[number];
