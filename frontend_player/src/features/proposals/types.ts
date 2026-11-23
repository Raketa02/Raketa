/**
 * **The proposals feature's only public surface** — a group's Games deck and a game's details
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2, A4.2; the mechanics
 * §6–§8), and the player's own two reads, Games & money and the live yeses
 * ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7.1, A7.3) — over the
 * backend's Proposals context (#538, #539).
 *
 * The group page draws `GamesDeck` as its Games tab and reads the tab's badge with `useGamesBadge`;
 * the details screen is mounted by its route file under `play/group/`, which checks its params
 * here first. The dependency points one way — `groups` reads `proposals`, never the reverse — so
 * the page hands in what only it knows: the kind its switch stands on, and the starting cards a
 * group with nothing dealt still draws.
 *
 * The shell composes `GamesAndMoneyRow` into the You tab's ACCOUNT group, and a route file under
 * `you/` mounts its screen. `LiveYeses` and `PaymentsToConfirm` are You › Payments' sections,
 * **handed to that screen by its route file** rather than imported by `payments`: the deck will open
 * the payment setup as a sheet (A2.4), so the edge between the two features points from here to
 * there.
 *
 * Since #556 it is Home's too: the booked games on the rail, a booked game's details, its chat and
 * its result — see the block below on Home.
 */

export { GamesDeck, type GamesDeckProps } from './components/GamesDeck';
export { GameDetailsScreen, type GameDetailsScreenProps } from './components/GameDetailsScreen';
export { GamesAndMoneyRow, type GamesAndMoneyRowProps } from './components/GamesAndMoneyRow';
export { GamesAndMoneyScreen } from './components/GamesAndMoneyScreen';
export { LiveYeses } from './components/LiveYeses';
export { PaymentsToConfirm } from './components/PaymentsToConfirm';
export { useGamesBadge } from './hooks/useGroupDeck';
/** What the group page's pull re-reads on Games, Fill in and You’re in — the tabs this feature draws. */
export { useRereadGroupGames } from './hooks/useGroupDeck';
/**
 * **A group's Fill in and You’re in tabs** (#557, split by #847) — the rescues, and the reader's own
 * live yeses, each drawn by the group page as a tab of its own with the badge its tab reads. The page
 * hands You’re in the starting card it draws once neither tab has a row, as it does the Games tab's.
 */
export { FillInBoard, type FillInBoardProps } from './components/FillInBoard';
export { YoureInBoard, type YoureInBoardProps } from './components/YoureInBoard';
export { useFillInBadge } from './hooks/useFillIn';
export { useYoureInBadge } from './hooks/useLiveYeses';
export { FILL_IN_COPY } from './components/fillInCopy';
export { parseGameDetailsParams } from './schemas/gameDetailsParams';
export type { GameKind } from './domain/vocabulary';
/** The words the group page's suites hold the tab to. */
export { PROPOSALS_COPY } from './components/proposalsCopy';

/**
 * **The moment a yes fills a game** (#555) — the ten seconds of *Undo*, the setup a first yes needs,
 * *It's a game!* and a refused share's confirmation. The shell mounts the provider around the tabs
 * for the session, because a yes said on the deck outlives the deck; the screens here reach it
 * through `useFill`, which does not cross. The words cross for the suites that walk it.
 */
export { FillProvider, type FillProviderProps } from './components/FillProvider';
export { FILL_COPY } from './components/fillCopy';

/**
 * ***Post a game*** (#558; the screens A5) — the screen, mounted over the group's page by `groups`,
 * which hands in the sports, the page's sport and its switch's kind; the route the page's two doors
 * push; and the draft's end, which the page calls when it goes. The words cross for the suites.
 */
export {
  PostAGameScreen,
  type PostAGameScreenProps,
  type PostingSport,
} from './components/PostAGameScreen';
export { postAGameRoute } from './components/proposalRoutes';
export { forgetPostDraft } from './store/postDraft.store';
export { POSTING_COPY } from './components/postingCopy';

/**
 * **Home's booked games, and a booked game in detail** (#556; the screens A4.1, A4.4, A8) — over
 * `GET /home` and `GET /bookings/{id}` (#542).
 *
 * Home is one rail of booked games (#576): the shell draws `HomeRail` under its own heading and
 * empty sentences, and puts `useHomeBadge`'s count on the bar. The details, the game's chat and its
 * result are each mounted by a route file under `booking/[bookingId]/`, which checks its param here
 * first; the routes themselves are this feature's to spell.
 */
export { HomeRail, type HomeRailProps } from './components/HomeRail';
export { useHomeBadge } from './hooks/useHome';
export { BookedGameScreen, type BookedGameScreenProps } from './components/BookedGameScreen';
export { BookedGameChat, type BookedGameChatProps } from './components/BookedGameChat';
export {
  BookedGameResult,
  type BookedGameResultProps,
  type PlayedWithInput,
} from './components/BookedGameResult';
export { parseBookingParams, parseRescueParams } from './schemas/bookingParams';
export { bookedGameRoute } from './components/proposalRoutes';
/**
 * **A friends game's empty seat** (#760): the group a seat may be opened to, whose name the details'
 * route reads from `groups` and hands in (`groupName`); and *Invite a friend*'s picker with one
 * seat, which the shell composes from `friends`' page and picker around the game (`SeatInvite`) and
 * the order (`InviteOrder`), at the route `parseSeatInviteParams` checks.
 */
export { useSeatOpeningGroup } from './hooks/useHome';
export { parseSeatInviteParams } from './schemas/bookingParams';
export {
  InviteOrder,
  NobodyToInvite,
  SeatInvite,
  type FriendPicked,
  type InviteOrderProps,
  type SeatInviteProps,
} from './components/SeatInvite';
export type { SeatToInvite } from './domain/friendsGame';
/** The words the Home and details suites hold the screens to. */
export { HOME_GAME_COPY } from './components/homeCopy';
/**
 * ***Leave the game*** — the departure's one word, on the door and on the sheet's act, for the
 * suites that press it. The sheet and its words are this feature's since
 * [#574](https://github.com/Raketa02/Raketa/issues/574), with the booked game's departure.
 */
export { LEAVE_THE_GAME } from './components/leaveSheetCopy';

/**
 * **Where a notice opens** ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens A9):
 * a game still filling's details, spelled here for the deck's own **i**, a booked game's open seat
 * seen from outside — a booked game's own is `bookedGameRoute`, above — and a booked game's result
 * screen, where each step at the court is acted on (#664); and the keys a tap re-reads, so the
 * screen it opens draws what the notice said rather than a read from before it, as `paymentKeys`
 * crosses for the fill. A notice arriving while the app is open re-reads Home's two reads
 * (`rereadHome`): the games, the bar's badge with them, and *TO CONFIRM*, in Needs your answer.
 */
export { bookedResultRoute, gameRoute, rescueRoute } from './components/proposalRoutes';
export { proposalKeys } from './hooks/proposalKeys';
export { rereadHome } from './hooks/useHome';

/**
 * **Home's friend requests** (#753) — they ride on `GET /home`, which this feature reads, and
 * `friends` draws them and answers them: the read and its type cross, and nothing else does.
 */
export { useHomeFriendRequests } from './hooks/useHome';
export type { HomeFriendRequest, RequestFoundBy } from './domain/home';

/**
 * **Home's asks for a level** (#765) — they ride on `GET /home` too: `friends` draws ASKED FOR A
 * LEVEL and answers it, and `groups`' Home card reads whether the row holds one, to leave *Get
 * your level* out. A level got drops its sport's card and re-reads Home (`rereadHomeAfterALevel`), which the
 * entry gate runs through the shell as a rating pass ends.
 */
export { rereadHomeAfterALevel, useHomeLevelAsks } from './hooks/useHome';
/**
 * **The trophy left of the bell** (#775) — the reader's ranking off Home's one read, which
 * `rankings` draws: the sport of the latest result and the places in it.
 */
export { useHomeRanking } from './hooks/useHome';
export type { HomeRanking } from './domain/home';
export type { HomeLevelAsk, HomeLevelAsker } from './domain/home';

/**
 * **Needs your answer's first two sections** (#817, ADR-0205 §1) — ***TO CONFIRM · n***, a tile per
 * payment to confirm, and ***FRIENDS GAME · n***, one invitation at a time on the paging rail (#759;
 * friends 12). They were Home's rows. The shell composes them in the sheet the header's envelope
 * opens, handing the bell's re-read to the invitations, since answering takes one off the bell; and
 * counts what waits in all four sections off Home's one read (`useAnswersWaiting`), the envelope's
 * badge with them (#819). When the sheet goes for good the shell records the visit through
 * `useNeedsYourAnswerVisit`, which names the watermark of the read the sheet showed, clears the badge
 * and reads Home again. The words cross for the suites that walk them.
 */
export { ToConfirmSection } from './components/ToConfirmSection';
export { FriendsGameSection, type FriendsGameSectionProps } from './components/FriendsGameSection';
export {
  useAnswersWaiting,
  useNeedsYourAnswerVisit,
  type AnswersWaiting,
} from './hooks/useNeedsYourAnswer';
export type { FriendsGamesWaiting } from './hooks/useHome';
export { FRIENDS_GAME_COPY } from './components/friendsGameCopy';
/**
 * **The fill, carried into a sheet** (#817) — read outside it (`useSheetFill`), provided again
 * inside it (`FillInASheet`), which also draws the fill's confirmation, setup and *It's a game!* over
 * it: a sheet keeps the root's contexts only, and a sheet opened from a sheet is drawn inside it.
 * `over` is what the fill has up, which Needs your answer steps aside under.
 */
export {
  FillInASheet,
  useSheetFill,
  type FillInASheetProps,
  type SheetFill,
} from './components/FillInASheet';
export type { FillOver } from './hooks/useFill';

/**
 * **The friends card and *Find a court*** (#757; the friends screens §7.2–§7.3) — the card a
 * group's Friends tab draws under its court once every seat is filled, over #750's two reads. The
 * group page composes it: it holds the line-up (`FriendsCardAsk`, structurally its own), hands in
 * the friends seated (`CardPerson`) and reads the same card (`useFriendsCard`) for the sides its
 * court draws, so the court and the card always name the same sides. The words cross for the
 * suites that walk it.
 */
export { FriendsCard, type FriendsCardProps } from './components/FriendsCard';
export { useFriendsCard } from './hooks/useFriendsCard';
export {
  refusalOf,
  type CardPerson,
  type FriendsCardAsk,
  type FriendsCardRefusal,
  type FriendsCourtPick,
} from './domain/friendsCard';
export { FRIENDS_CARD_COPY } from './components/friendsCardCopy';
