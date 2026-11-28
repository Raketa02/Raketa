/**
 * How a **counted** game ended, for the one person a surface is about.
 *
 * Two values and no third. There is no draw in a racket sport, and a game nobody agreed a
 * score for is not here at all — it is *an evening rather than evidence*, so it is counted in
 * `countedGames` and absent from the run of form
 * ([ADR-0137](../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
 *
 * **No moment travels beside one of these.** A run of results is outcomes in order, which is a
 * run of form rather than a statement about when anybody was last here — activity recency at
 * any granularity is row three of the Liveness table and
 * [ADR-0106](../../../../docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)
 * §5 refuses it.
 *
 * ## Why this is `shared/` and not `play/domain/`
 *
 * It began in `features/play/domain/vocabulary.ts`, because the competitive candidate card was
 * the only thing that had ever drawn a run of five. It is here now for `playIntent.ts`'s
 * reason and on `shared/README.md`'s own test — *"whether a second feature would have written
 * the identical table"*. The record sheet draws the same run
 * ([#373](https://github.com/Rakieta02/Rakieta/issues/373)), and it would have written this list
 * of two exactly; what a win and a loss **are** is fixed by ADR-0137 rather than by either
 * surface that prints one.
 *
 * The move is what lets [7.13](../../../docs/design-system.md#713-the-record-block)'s run of
 * squares be one drawn object in `shared/ui` rather than a copy per card. What each feature
 * *does* with an outcome stays behind: which run a card is served, and the clause a listener
 * gets counting them, are still `features/play/`'s.
 *
 * The wire spells these identically, so there is no second spelling and no mapper of its own:
 * the agreement with the contract is asserted by the compiler in
 * `features/play/mappers/wireVocabulary.ts`, and narrowing a served string against this list
 * is `candidateMappers`'.
 */

/**
 * The two outcomes, and the runtime membership test beside the type.
 *
 * The type is derived from the list rather than declared beside it, so the two cannot
 * disagree — `SOCIAL_TAG_IDS`' shape, and for its reason: the array is what a build eight
 * months old needs the day a third value it has never seen arrives on the wire.
 */
export const GAME_RESULTS = ['WIN', 'LOSS'] as const;

export type GameResult = (typeof GAME_RESULTS)[number];
