/**
 * The `challenges` feature's only public surface.
 *
 * It begins as the words a challenge says, because the copy deck was settled before the send
 * was built ([#262](https://github.com/Raketa02/Raketa/issues/262)) and a standing's sentence
 * belongs to the context that owns a challenge rather than to the tab that starts one. The
 * **send** landed with [#274](https://github.com/Raketa02/Raketa/issues/274) and is the rest of
 * it: `SH.propose`, the mutation behind it, the rule that says which source a refusal sends the
 * court off to re-read, and the sentences all three write.
 *
 * **The list finally has a surface** ([#360](https://github.com/Raketa02/Raketa/issues/360)):
 * `GET /challenges` had exactly one reader — the naming a refused send needs — and now has
 * three, because the Chats tab draws it and the tab bar counts it. So two things cross this
 * seam that did not: the section the shell composes, and the number the bar is handed.
 */

export {
  STANDINGS,
  type ChallengeSide,
  type Standing,
  type StandingFacts,
} from './domain/standing';
export {
  A_PAIR_HERE_IS_ALREADY_PLAYING,
  CHALLENGE_SENT,
  LINE_UP_CHANGED,
  MUTUAL_YES,
  NOBODY_IS_CONTACTED_YET,
  NOTHING_MARKED_AFTER_THE_REFRESH,
  PROPOSE_SHEET_TITLE,
  SENDING_LABEL,
  SEND_CHALLENGE_LABEL,
  answerWindowLine,
  openChallengeLine,
  proposeClosing,
  standingLine,
} from './components/challengePresentation';
export { challengeErrorMessage } from './components/challengeErrorMessage';

/**
 * **The pre-send sheet**, drawn by the court and by nothing else.
 *
 * The court's pinned CTA opens it; confirming dismisses it and runs the send, whose pending
 * state and whose refusal both belong to that CTA rather than to a modal over the seats the
 * player has to change ([#239](https://github.com/Raketa02/Raketa/issues/239) §5).
 */
export { ProposeSheet, type ProposeSheetProps } from './components/ProposeSheet';

/**
 * What a refused send costs the screen next — **a re-read, and never a payload.**
 *
 * The court holds both re-reads because both sources are already its own: the origin search is
 * under `searchKeys.detail(id)`, and the player's own challenges are one hook away. This is the
 * rule that says which.
 */
export { sendRefusal, type SendRefusal } from './domain/sendRefusal';

/**
 * The send itself, and the read that names the pair a refusal would not.
 *
 * `CHALLENGE_MUTATION_OPTIONS` stays internal: it is this feature's own configuration, and every
 * caller it will ever have is an act of this feature's.
 */
export { useOpenPair, useSendChallenge } from './hooks/useChallenges';

/**
 * **The Chats tab's `CHALLENGES` section**, and the one number the tab bar draws.
 *
 * The section is composed by the shell under the tab's own words, exactly as `GamesSection` is
 * composed on Now: the tab owns its citation and nothing that is drawn under it. It is handed
 * the empty line because that sentence is about the *screen* rather than about a challenge.
 *
 * The count is a **hook and not a component**, because `shared/ui` may not import a feature: a
 * bar that read this hook would invert the dependency and give *"the drawn object only"* a
 * network call ([#326](https://github.com/Raketa02/Raketa/issues/326) §10). The shell mounts it
 * and passes a number.
 */
export { ChallengesSection, type ChallengesSectionProps } from './components/ChallengesSection';
export { useChallengesWaiting } from './hooks/useChallenges';

/**
 * **The screen a row opens, and the two answers on it** — mounted by
 * `/chats/challenge/[challengeId]` ([#361](https://github.com/Raketa02/Raketa/issues/361)).
 *
 * A state-keyed surface over the six standings and two sides. Everything under it stays
 * internal: the read, the answer, the fold they are both keyed on and the words the screen
 * writes are this feature's, and the only things a route needs are the screen and the check on
 * the id it hands over.
 */
export { ChallengeScreen, type ChallengeScreenProps } from './components/ChallengeScreen';

/**
 * The route's own check on the id it is handed, because a route param is attacker-controlled and
 * this one becomes the path of a `POST` that accepts a game on somebody's behalf.
 */
export { parseChallengeRouteParams, type ChallengeRouteParams } from './schemas/routeParams';

/**
 * The court a send carries — the shape the builder hands over, and the only type of this
 * feature's that crosses the seam.
 *
 * `SendAsk` and `SentChallenge` stay internal: the ask is built by the one hook that takes it
 * and the answer is read by nobody, because success replaces the stack and the challenge is
 * read back off `GET /challenges` like anybody else's.
 */
export type { ProposedCourt } from './mappers/challengeMappers';
