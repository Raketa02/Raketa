/**
 * The `challenges` feature's only public surface.
 *
 * It begins as the words a challenge says, because the copy deck was settled before the send
 * was built ([#262](https://github.com/Raketa02/Raketa/issues/262)) and a standing's sentence
 * belongs to the context that owns a challenge rather than to the tab that starts one. The
 * send, the list and their screens land with
 * [#274](https://github.com/Raketa02/Raketa/issues/274).
 */

export { STANDINGS, type ChallengeSide, type Standing } from './domain/standing';
export {
  MUTUAL_YES,
  NOBODY_IS_CONTACTED_YET,
  answerWindowLine,
  proposeClosing,
  standingLine,
  type StandingFacts,
} from './components/challengePresentation';
