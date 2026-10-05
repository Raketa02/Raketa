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
 * A state-keyed surface over the seven standings and two sides. Everything under it stays
 * internal: the read, the answer, the fold they are both keyed on and the words the screen
 * writes are this feature's, and the only things a route needs are the screen and the check on
 * the id it hands over.
 */
export { ChallengeScreen, type ChallengeScreenProps } from './components/ChallengeScreen';

/**
 * **The fill's send** — `POST /challenges/{id}/seats`, called from the builder this screen
 * pushed ([#362](https://github.com/Raketa02/Raketa/issues/362)).
 *
 * It crosses the seam for `useSendChallenge`'s own reason and is the same seam read a second
 * time: *the one action in this tab that reaches another person* is this feature's, wherever the
 * control that carries it out is drawn. The builder calls it and pops back; everything it says
 * and everything a refusal costs stay here.
 */
export { useInviteSeats } from './hooks/useChallenge';

/**
 * The route's own check on the id it is handed, because a route param is attacker-controlled and
 * this one becomes the path of a `POST` that accepts a game on somebody's behalf.
 */
export { parseChallengeRouteParams, type ChallengeRouteParams } from './schemas/routeParams';

/**
 * **The yes screen** — mounted by `/chats/challenge/[challengeId]/yes`
 * ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md),
 * [#433](https://github.com/Raketa02/Raketa/issues/433),
 * [#434](https://github.com/Raketa02/Raketa/issues/434)): the screen a yes lands on — the
 * faces, one word, two doors — pushed by the challenge screen the instant *I'm in* is answered,
 * and by the deck's yes the instant *Let's play* comes back mutual and naming a chat. The route
 * hands over the id and *which yes*, both checked first; `yesRoute` is what the deck pushes;
 * the fold, the tile, the entrance and the words stay internal.
 */
export { YesScreen, type YesScreenProps } from './components/YesScreen';
export {
  parseYesRouteParams,
  yesRoute,
  type WhichYes,
  type YesRouteParams,
} from './schemas/routeParams';

/**
 * **The yes screen's second face's words, exported for the suite that walks it from the deck.**
 *
 * `deck.test.tsx` drives *Let's play* through the real route tree and asserts what the phone says
 * when the reply comes back mutual — the word, the sentence and the second door — and a test
 * spelling *Matched!* as a literal is a red build for the ticket that rewords it, which is the
 * rule every copy deck in this app is read through. Nothing in `src/` outside this feature reads
 * any of the three.
 */
export { LATER, MATCHED_WORD, matchedAnnouncement } from './components/yesScreenPresentation';

/**
 * The court a send carries — the shape the builder hands over, and the only type of this
 * feature's that crosses the seam.
 *
 * `SendAsk` and `SentChallenge` stay internal: the ask is built by the one hook that takes it
 * and the answer is read by nobody, because success replaces the stack and the challenge is
 * read back off `GET /challenges` like anybody else's.
 */
export type { ProposedCourt } from './mappers/challengeMappers';
/**
 * **The departure's door, for a Chats row** — the one place a game is left from
 * ([#427](https://github.com/Raketa02/Raketa/issues/427), ADR-0165 §6,
 * [ADR-0175](../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §4). A door rather than a control: the row decides what a door looks like there — the button a
 * swipe reveals, and the accessibility action a listener takes in its place — and this hands it
 * the word, the way to open the sheet, and the sheet itself, drawn beside whatever the row drew.
 * **Composed by the shell** into the conversations section rather than imported by it, on
 * ADR-0149's shape: the act is this feature's and the row is that one's, and a feature importing
 * a feature that imports it is the cycle Part 1 calls a defect. The game screen's *Leave this
 * game* and the challenge screen's door are gone: leaving is one gesture in one place.
 */
export { DepartureDoor, type DepartureDoorProps } from './components/DepartureDoor';

/**
 * **The fill, for the game screen and the Now card** — the challenge screen's ⚡ pressed on a game
 * ([#419](https://github.com/Raketa02/Raketa/issues/419)): the same search, the same builder under
 * the challenge, and the seats already taken read off the game by whoever composes it. One
 * control for the card's wide door and the act directly under the card on the screen (ADR-0175
 * §4), because they are one press.
 */
export { FillTheSeat, type FillTheSeatProps } from './components/FillTheSeat';

/**
 * **The departure's word, exported for the suite that walks the plan lead from `plans`.**
 *
 * `gameScreenPlanLead.test.tsx` asserts that the game screen draws no leave and no call-off any
 * more (ADR-0175 §1, §4), and a test spelling *Leave the game* as a literal is a red build for
 * the ticket that rewords it — `findAGamePresentation`'s rule, the one every copy deck in this
 * app is read through. Nothing in `src/` outside this feature reads it otherwise.
 */
export { LEAVE_THE_GAME } from './components/leaveGamePresentation';
/**
 * **The departure's sheet** — *Before you leave*, *Stay in*, the act named once — crossed for a
 * booked game's *Leave the game* (#557: *today's Before you leave sheet with the new words*), which
 * hands it its own body.
 */
export { LeaveSheet, type LeaveSheetProps } from './components/LeaveSheet';

/**
 * **This feature's list key, and the one write to it another feature may make** — crossed for the
 * dismissal, the act on `games` that clears a called-off court from the reader's two lists at once
 * ([ADR-0173](../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md)).
 *
 * The **key** crosses on `gameKeys`' argument in the other direction: what `features/games` owes
 * this list is the statement that it is now out of date, and spelling `['challenges']` at the call
 * site would be the same coupling with nothing holding the two spellings equal. The **drop**
 * crosses on `dropRoomOfChallenge`'s: the reply has told the client the row is gone, so it goes on
 * the reply, and which rows a game id touches is decided here where the row's shape is known. The
 * query does not cross — a game act has no business reading a challenge.
 */
export { dropCourtOfGame } from './hooks/challengeCache';
export { challengeKeys } from './hooks/challengeKeys';

/**
 * **The court the reader shares with one person**, for the radar's record sheet
 * ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4, [#464](https://github.com/Raketa02/Raketa/issues/464)): a live challenge or game the two
 * are on, or one just behind them, read off this feature's own list by its own pair rule
 * (`domain/courtWith`). What crosses is the court's id and its standing as it reads to the
 * reader — `StandingFacts`, which `standingLine` above already turns into the row's sentence —
 * so the sheet's foot names the court in this feature's words and never composes its own.
 */
export { useCourtWith, type CourtWith } from './hooks/useChallenges';

/**
 * **The yes screen's drawn parts, for its third face** — *It's a game!*, the yes that filled a game
 * dealt in a group's deck ([#555](https://github.com/Raketa02/Raketa/issues/555); the Games & Fill
 * in screens A2.4: *today's yes screen, with the new word*). The ground, the entrance's one beat and
 * the tile cross, and nothing else: the faces there come off the card the yes was said on, the
 * doors open a game rather than a room, and the reads, the folds and the words stay here.
 */
export { YesEntrance, type YesEntranceProps } from './components/YesEntrance';
export { YesGround } from './components/YesGround';
export { YesTile, type YesTileProps } from './components/YesTile';
export type { YesSeat } from './domain/yesScreen';
